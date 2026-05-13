from hypergraph import Graph, SyncRunner, node

from furever_match.db_ingestion import supabase
from furever_match.matching import calculate_match_score


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


@node(output_name=("filtered", "filter_relaxed"))
def hard_filter(candidates: list, adoption_request: dict) -> tuple:
    def _apply(dogs, relaxed=False):
        result = list(dogs)
        if not relaxed:
            if adoption_request.get("requested_gender"):
                result = [
                    d for d in result
                    if not d.get("gender") or d["gender"] == adoption_request["requested_gender"]
                ]
            if adoption_request.get("requested_size"):
                result = [
                    d for d in result
                    if not d.get("size") or d["size"] == adoption_request["requested_size"]
                ]
        if adoption_request.get("has_kids"):
            result = [d for d in result if d.get("get_along_with_kids") is not False]

        which_pets = (adoption_request.get("which_pets") or "").lower()
        if adoption_request.get("has_other_pets"):
            if "חתול" in which_pets or "cat" in which_pets:
                result = [d for d in result if d.get("get_along_with_cats") is not False]
            if "כלב" in which_pets or "dog" in which_pets:
                result = [d for d in result if d.get("get_along_with_dogs") is not False]
        return result

    filtered = _apply(candidates, relaxed=False)
    if filtered:
        return filtered, False

    # No results — relax gender/size constraints and retry
    filtered = _apply(candidates, relaxed=True)
    return filtered, True


@node(output_name="scored")
def score_dogs(filtered: list, adoption_request: dict) -> list:
    results = []
    for dog in filtered:
        match = calculate_match_score(dog, adoption_request)
        results.append({
            **dog,
            "match_score": match["score"],
            "match_details": match["details"],
        })
    return sorted(results, key=lambda r: r["match_score"], reverse=True)


@node(output_name="top3")
def llm_explain(scored: list, adoption_request: dict) -> list:
    # Stub — Phase 3 will add real Hebrew LLM explanations
    return [{**dog, "explanation": ""} for dog in scored[:3]]


match_graph = Graph(nodes=[load_request, load_dogs, hard_filter, score_dogs, llm_explain])
_runner = SyncRunner()


def run_match_graph(request_id: str) -> dict:
    result = _runner.run(match_graph, request_id=request_id)
    return result.values
