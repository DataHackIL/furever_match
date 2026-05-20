from hypergraph import Graph, SyncRunner, node

from furever_match.db_ingestion import supabase
from furever_match.matching_v2 import calculate_match_score_v2


@node(output_name="adoption_request")
def load_request(request_id: str) -> dict:
    resp = (
        supabase.table("adoption_requests")
        .select("*")
        .eq("id", request_id)
        .single()
        .execute()
    )
    return resp.data or {}


@node(output_name="candidates")
def load_dogs(adoption_request: dict) -> list:
    dogs_resp = supabase.table("dogs").select("*").eq("status", "available").execute()
    dogs = dogs_resp.data or []

    dog_ids = [d["id"] for d in dogs]
    images_resp = (
        supabase.table("dog_images")
        .select("dog_id,image_url")
        .in_("dog_id", dog_ids)
        .execute()
    )
    first_image = {}
    for row in images_resp.data or []:
        if row["dog_id"] not in first_image:
            first_image[row["dog_id"]] = row["image_url"]

    for dog in dogs:
        dog["image_url"] = first_image.get(dog["id"])
    return dogs


@node(output_name="scored")
def score_dogs(candidates: list, adoption_request: dict) -> list:
    results = []
    for dog in candidates:
        match = calculate_match_score_v2(dog, adoption_request, use_llm=False)
        results.append({
            **dog,
            "passes_filters": match["passes_filters"],
            "filter_rejection_reason": match["filter_rejection_reason"],
            "match_score": match["final_score"],
            "soft_scores_breakdown": match["soft_scores_breakdown"],
        })
    return sorted(results, key=lambda r: r["match_score"], reverse=True)


@node(output_name="top3")
def top3(scored: list) -> list:
    return [d for d in scored if d["passes_filters"]][:3]


match_graph = Graph(nodes=[load_request, load_dogs, score_dogs, top3])
_runner = SyncRunner()


def run_match_graph(request_id: str) -> dict:
    result = _runner.run(match_graph, request_id=request_id)
    return result.values
