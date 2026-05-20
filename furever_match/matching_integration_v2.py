"""
Enhanced Matching Integration v2

Pipeline:
  1. Hard filter + soft score all dogs (no LLM).
  2. Take top-N passing dogs by soft score.
  3. One LLM call to extract person features.
  4. One LLM call per top-N dog to score similarity against pre-computed dog features.
     Falls back to full 2-step extraction if pre-computed features are missing.
  5. Re-rank by final (soft + LLM) score.
"""

from furever_match.db_ingestion import supabase
from furever_match.llm import get_llm_client
from furever_match.matching_v2 import (
    calculate_match_score_v2,
    check_filter_dominance,
    check_hard_filters,
    calculate_soft_scores,
    _weighted_average,
    extract_person_features,
    load_matching_config,
)


_LEVEL_ORDER = ["low", "medium", "high"]

def _level_score(a: str, b: str) -> float:
    """Return 1.0 for exact match, 0.5 for 1-step apart, 0.0 for 2+ steps."""
    a, b = (a or "").lower(), (b or "").lower()
    if a not in _LEVEL_ORDER or b not in _LEVEL_ORDER:
        return 0.6  # neutral when unknown
    dist = abs(_LEVEL_ORDER.index(a) - _LEVEL_ORDER.index(b))
    return [1.0, 0.5, 0.0][dist]


def _build_character_match(dog_features: dict, person_features: dict,
                            soft_avg: float, rejection_reason: str = None) -> dict:
    """
    Score personality compatibility locally using pre-computed dog features
    and LLM-extracted person features — no extra LLM call needed.
    """
    if rejection_reason:
        return {
            "compatibility_score": 0,
            "key_strengths": [],
            "potential_concerns": [rejection_reason],
            "reasoning": f"Disqualified: {rejection_reason}",
            "recommendation": "",
        }

    if not dog_features or not person_features:
        return {
            "compatibility_score": soft_avg,
            "key_strengths": [],
            "potential_concerns": [],
            "reasoning": "",
            "recommendation": "",
        }

    scores = []

    # Activity level alignment
    act_score = _level_score(dog_features.get("activity_level"), person_features.get("activity_level"))
    scores.append(act_score)

    # Care requirements vs person's time availability.
    # Having MORE time than the dog needs is always fine; shortage is penalised.
    care = (dog_features.get("care_requirements") or "").lower()
    time_avail = (person_features.get("time_availability") or "").lower()
    if care in _LEVEL_ORDER and time_avail in _LEVEL_ORDER:
        care_idx = _LEVEL_ORDER.index(care)
        time_idx = _LEVEL_ORDER.index(time_avail)
        if time_idx >= care_idx:
            scores.append(1.0)
        else:
            scores.append(max(0.0, 1.0 - (care_idx - time_idx) * 0.5))

    # Experience level: novice person + high-needs dog = concern
    exp = (person_features.get("experience_level") or "").lower()
    needs = dog_features.get("needs") or []
    if exp == "beginner" and isinstance(needs, list) and len(needs) > 3:
        scores.append(0.4)
    elif exp in ("intermediate", "experienced"):
        scores.append(0.9)

    # Blend toward soft_avg when few data points — one mismatch shouldn't dominate
    if scores:
        raw = (sum(scores) / len(scores)) * 100
        confidence = min(1.0, len(scores) / 3.0)   # full confidence at 3+ signals
        personality_score = round(raw * confidence + soft_avg * (1 - confidence))
    else:
        personality_score = round(soft_avg)

    traits  = dog_features.get("personality_traits") or []
    fears   = dog_features.get("fears_sensitivities") or []
    motives = person_features.get("motivations") or []

    strengths = traits[:2] if isinstance(traits, list) else []
    concerns  = fears[:1]  if isinstance(fears,  list) else []

    ideal = dog_features.get("ideal_owner_profile", "")
    lifestyle = person_features.get("lifestyle", "")

    return {
        "compatibility_score": personality_score,
        "key_strengths":       strengths,
        "potential_concerns":  concerns,
        "reasoning":           ideal,
        "recommendation":      lifestyle,
    }


def get_matching_dogs_v2(
    request_id: str,
    use_llm: bool = True,
    llm_provider: str = None,
    min_score: float = 0.0,
) -> dict:
    try:
        req_resp = supabase.table("adoption_requests").select("*").eq("id", request_id).single().execute()
        if not req_resp.data:
            return {"matches": [], "filter_warnings": []}
        adoption_request = req_resp.data

        dogs_resp = supabase.table("dogs").select("*").eq("status", "available").execute()
        dogs = dogs_resp.data or []

        dog_ids = [d["id"] for d in dogs]
        if dog_ids:
            images_resp = supabase.table("dog_images").select("dog_id,image_url").in_("dog_id", dog_ids).execute()
            first_image = {}
            for row in (images_resp.data or []):
                if row["dog_id"] not in first_image:
                    first_image[row["dog_id"]] = row["image_url"]
        else:
            first_image = {}

        cfg = load_matching_config()
        weights = cfg["final_score"]
        soft_rules = cfg["soft_rules"]
        llm_cfg = cfg["llm_analysis"]
        llm_enabled = llm_cfg["enabled"]
        llm_top_n = llm_cfg.get("llm_top_n", 10)
        fallback_score = llm_cfg["fallback_score"]
        if llm_provider is None:
            llm_provider = llm_cfg.get("default_provider", "ollama")

        dominance_warnings = check_filter_dominance(dogs, adoption_request)

        # ── Step 1: hard filter + soft score all dogs ──────────────────────
        scored = []
        for dog in dogs:
            passes, reason = check_hard_filters(dog, adoption_request)
            soft_scores = {}
            soft_avg = 0.0
            if passes:
                soft_scores = calculate_soft_scores(dog, adoption_request)
                soft_avg = _weighted_average(soft_scores, soft_rules)
            scored.append({
                "dog": dog,
                "passes": passes,
                "reason": reason,
                "soft_scores": soft_scores,
                "soft_avg": soft_avg,
            })

        scored.sort(key=lambda x: x["soft_avg"], reverse=True)

        # ── Step 2: 1 LLM call (person features) + load pre-computed dog features
        person_features = {}
        dog_features_map = {}

        if use_llm and llm_enabled:
            top_passing_ids = [
                s["dog"]["id"] for s in scored if s["passes"]
            ][:llm_top_n]

            if top_passing_ids:
                try:
                    rows = (
                        supabase.table("dog_llm_features")
                        .select("dog_id, features")
                        .in_("dog_id", top_passing_ids)
                        .execute()
                        .data or []
                    )
                    dog_features_map = {r["dog_id"]: r["features"] for r in rows}
                except Exception as e:
                    print(f"[WARN] dog_llm_features table unavailable: {e}")

            try:
                llm_client = get_llm_client(provider=llm_provider)
                step_cfg = llm_cfg["steps"]["feature_extraction"]
                person_features = extract_person_features(adoption_request, llm_client, step_cfg)
            except Exception as e:
                print(f"[WARN] Person feature extraction failed: {e}")

        # ── Step 3: build result list ──────────────────────────────────────
        results = []
        for entry in scored:
            dog = entry["dog"]
            passes = entry["passes"]
            reason = entry["reason"]
            soft_scores = entry["soft_scores"]
            soft_avg = entry["soft_avg"]

            if not passes and soft_avg < min_score:
                continue

            precomputed = dog_features_map.get(dog["id"]) if passes else None
            character_match = _build_character_match(
                precomputed, person_features, soft_avg, reason if not passes else None
            )

            final_score = (
                soft_avg * weights["soft_weight"]
                + character_match["compatibility_score"] * weights["llm_weight"]
            ) if passes else 0.0

            results.append({
                "dog_id":    dog["id"],
                "dog_name":  dog.get("name"),
                "breed":     dog.get("breed"),
                "size":      dog.get("size"),
                "gender":    dog.get("gender"),
                "age":       dog.get("age"),
                "description": dog.get("description"),
                "image_url": first_image.get(dog["id"]),

                "passes_filters":          passes,
                "filter_rejection_reason": reason,

                "soft_score":             round(soft_avg, 2),
                "soft_scores_breakdown":  {k: round(v * 100, 2) for k, v in soft_scores.items()},

                "character_match": character_match,

                "match_score":     round(final_score, 2),
                "match_reasoning": " | ".join([
                    f"Soft matching score: {round(soft_avg, 2)}%",
                    f"Character compatibility: {character_match.get('compatibility_score', fallback_score)}%",
                    f"LLM analysis: {character_match.get('reasoning', '')}",
                ]),
            })

        return {
            "matches": sorted(results, key=lambda r: r["match_score"], reverse=True),
            "filter_warnings": dominance_warnings,
        }

    except Exception as e:
        print(f"Error in get_matching_dogs_v2: {e}")
        import traceback; traceback.print_exc()
        return {"matches": [], "filter_warnings": []}


def get_matching_dogs(
    request_id: str,
    use_llm: bool = True,
    llm_provider: str = "gemini",
) -> dict:
    return get_matching_dogs_v2(request_id, use_llm=use_llm, llm_provider=llm_provider)
