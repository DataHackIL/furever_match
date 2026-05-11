from furever_match.db_ingestion import supabase
from furever_match.matching import calculate_match_score


def get_matching_dogs(request_id: str) -> list:
    """
    Fetch adoption request, score all available dogs, return sorted list.
    """
    req_resp = supabase.table("adoption_requests").select("*").eq("id", request_id).single().execute()
    if not req_resp.data:
        return []
    adoption_request = req_resp.data

    dogs_resp = supabase.table("dogs").select("*").eq("status", "available").execute()
    dogs = dogs_resp.data or []

    # Fetch first image for each dog in one query
    dog_ids = [d["id"] for d in dogs]
    images_resp = supabase.table("dog_images").select("dog_id,image_url").in_("dog_id", dog_ids).execute()
    first_image = {}
    for row in (images_resp.data or []):
        if row["dog_id"] not in first_image:
            first_image[row["dog_id"]] = row["image_url"]

    results = []
    for dog in dogs:
        match = calculate_match_score(dog, adoption_request)
        results.append({
            "dog_id": dog["id"],
            "dog_name": dog.get("name"),
            "breed": dog.get("breed"),
            "size": dog.get("size"),
            "gender": dog.get("gender"),
            "age": dog.get("age"),
            "description": dog.get("description"),
            "image_url": first_image.get(dog["id"]),
            "match_score": match["score"],
            "match_details": match["details"],
        })

    return sorted(results, key=lambda r: r["match_score"], reverse=True)
