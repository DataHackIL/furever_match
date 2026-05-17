"""
Enhanced Matching Integration v2

Uses the new matching system with hard filters, soft scoring, and LLM reasoning.
"""

from furever_match.db_ingestion import supabase
from furever_match.matching_v2 import calculate_match_score_v2


def get_matching_dogs_v2(
    request_id: str,
    use_llm: bool = True,
    llm_provider: str = "gemini",
    min_score: float = 0.0
) -> list:
    """
    Fetch adoption request, score all available dogs with enhanced matching, return sorted list.

    Args:
        request_id: UUID of adoption request
        use_llm: Whether to use LLM for character analysis (default: True)
        llm_provider: "gemini" or "ollama" (default: "gemini")
        min_score: Minimum final score to include (0-100, default: 0)

    Returns:
        List of dogs sorted by final match score (highest first)
    """
    try:
        req_resp = supabase.table("adoption_requests").select("*").eq("id", request_id).single().execute()
        if not req_resp.data:
            return []
        adoption_request = req_resp.data

        dogs_resp = supabase.table("dogs").select("*").eq("status", "available").execute()
        dogs = dogs_resp.data or []

        # Fetch first image for each dog
        dog_ids = [d["id"] for d in dogs]
        if dog_ids:
            images_resp = supabase.table("dog_images").select("dog_id,image_url").in_("dog_id", dog_ids).execute()
            first_image = {}
            for row in (images_resp.data or []):
                if row["dog_id"] not in first_image:
                    first_image[row["dog_id"]] = row["image_url"]
        else:
            first_image = {}

        results = []
        for dog in dogs:
            match = calculate_match_score_v2(
                dog,
                adoption_request,
                use_llm=use_llm,
                llm_provider=llm_provider
            )

            # Skip if doesn't meet minimum score or fails hard filters
            if match['final_score'] < min_score and match['passes_filters'] is False:
                continue

            results.append({
                "dog_id": dog["id"],
                "dog_name": dog.get("name"),
                "breed": dog.get("breed"),
                "size": dog.get("size"),
                "gender": dog.get("gender"),
                "age": dog.get("age"),
                "description": dog.get("description"),
                "image_url": first_image.get(dog["id"]),

                # Hard filter info
                "passes_filters": match['passes_filters'],
                "filter_rejection_reason": match['filter_rejection_reason'],

                # Soft scores
                "soft_score": match['soft_score'],
                "soft_scores_breakdown": match['soft_scores_breakdown'],

                # Character match (from LLM)
                "character_match": match['character_match'],

                # Final score
                "match_score": match['final_score'],
                "match_reasoning": match['final_reasoning'],
            })

        # Sort by final score (highest first)
        return sorted(results, key=lambda r: r["match_score"], reverse=True)

    except Exception as e:
        print(f"Error in get_matching_dogs_v2: {e}")
        return []


def get_matching_dogs(
    request_id: str,
    use_llm: bool = True,
    llm_provider: str = "gemini"
) -> list:
    """
    Backward compatible wrapper - calls v2 matching by default.
    Set use_llm=False to use only soft scoring (faster).
    """
    return get_matching_dogs_v2(
        request_id,
        use_llm=use_llm,
        llm_provider=llm_provider
    )
