"""
Enhanced Matching System v2

Features:
1. Hard Filters: Clear criteria that disqualify dogs
2. Soft Scoring: Intelligent matching percentages
3. LLM Reasoning: Character and personality matching with explanations

All rule parameters are loaded from matching_rules.yaml.
"""

import json
import os
import yaml
from typing import Dict, List, Tuple, Optional
from furever_match.llm import get_llm_client

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "matching_rules.yaml")
_config_cache: Optional[Dict] = None


def load_matching_config() -> Dict:
    global _config_cache
    if _config_cache is None:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = yaml.safe_load(f)
    return _config_cache


# ============================================================
# PART 1: HARD FILTERS (Disqualifying Factors)
# ============================================================

def check_hard_filters(dog: Dict, adoption_request: Dict) -> Tuple[bool, Optional[str]]:
    """
    Apply hard filters that completely disqualify a dog.
    Returns: (passes_filters: bool, reason_if_rejected: str or None)
    """
    cfg = load_matching_config()["hard_rules"]

    # --- pets_compatibility ---
    pc = cfg["pets_compatibility"]
    if pc["enabled"] and adoption_request.get("has_other_pets") is True:
        which_pets = adoption_request.get("which_pets", "").lower()
        for check in pc["checks"].values():
            if check["trigger_contains"] in which_pets:
                if dog.get(check["dog_field"]) is False:
                    return False, check["rejection_message"]

    # --- kids_compatibility ---
    kc = cfg["kids_compatibility"]
    if kc["enabled"] and adoption_request.get("has_kids") is True:
        threshold = kc["young_kids_age_threshold"]
        has_young_kids = not _has_only_older_kids(
            adoption_request.get("kids_age", ""), threshold
        )
        if has_young_kids and dog.get(kc["dog_field"]) is False:
            return False, kc["rejection_message"]

    # --- training_requirements ---
    tr = cfg["training_requirements"]
    if tr["enabled"]:
        dog_training = dog.get(tr["dog_training_level_field"], "").lower()
        person_training = adoption_request.get(tr["person_training_level_field"], "").lower()
        for combo in tr["incompatible_combinations"]:
            if combo["dog_level"] in dog_training and combo["max_person_level"] in person_training:
                return False, tr["rejection_message"]

    # --- home_size_requirements ---
    hs = cfg["home_size_requirements"]
    if hs["enabled"]:
        dog_size = dog.get(hs["dog_size_field"], "").lower()
        has_house = adoption_request.get(hs["person_house_field"], False)
        for rule in hs["size_rules"]:
            if rule["dog_size"] in dog_size and rule["requires_house"] and not has_house:
                return False, rule["rejection_message"]

    return True, None


def _has_only_older_kids(kids_age: str, threshold: int = 15) -> bool:
    """Check if all kids are at or above the age threshold."""
    if not kids_age:
        return False
    for age in kids_age.split(","):
        try:
            if int(age.strip()) < threshold:
                return False
        except ValueError:
            pass
    return True


# ============================================================
# PART 2: SOFT SCORING (Matching Percentages)
# ============================================================

def score_gender(dog_gender: Optional[str], requested_gender: Optional[str]) -> float:
    sc = load_matching_config()["soft_rules"]["gender"]["scoring"]
    if not requested_gender:
        return sc["no_preference"]
    if not dog_gender:
        return sc["unknown"]
    return sc["match"] if dog_gender == requested_gender else sc["mismatch"]


def score_size(dog_size: Optional[str], requested_size: Optional[str]) -> float:
    rule = load_matching_config()["soft_rules"]["size"]
    sc = rule["scoring"]
    if not requested_size:
        return sc["unknown"]
    if not dog_size:
        return sc["unknown"]

    order = rule["size_order"]
    dog_s = dog_size.lower().strip()
    req_s = requested_size.lower().strip()

    if dog_s == req_s:
        return sc["exact_match"]
    if dog_s in order and req_s in order:
        dist = abs(order.index(dog_s) - order.index(req_s))
        return max(sc["min_score"], sc["exact_match"] - dist * sc["penalty_per_step"])
    return sc["unknown"]


def score_energy_level(dog_energy: Optional[str], requested_energy: Optional[str]) -> float:
    rule = load_matching_config()["soft_rules"]["energy_level"]
    sc = rule["scoring"]
    if not requested_energy:
        return sc["unknown"]
    if not dog_energy:
        return sc["unknown"]

    order = rule["energy_order"]
    dog_e = dog_energy.lower().strip()
    req_e = requested_energy.lower().strip()

    if dog_e == req_e:
        return sc["exact_match"]
    if dog_e in order and req_e in order:
        dist = abs(order.index(dog_e) - order.index(req_e))
        return max(sc["min_score"], sc["exact_match"] - dist * sc["penalty_per_step"])
    return sc["unknown"]


def score_training_level(dog_training: Optional[str], requested_training: Optional[str]) -> float:
    rule = load_matching_config()["soft_rules"]["training_level"]
    sc = rule["scoring"]
    if not requested_training:
        return sc["unknown"]
    if not dog_training:
        return sc["unknown"]

    order = rule["training_order"]
    dog_t = dog_training.lower().strip()
    req_t = requested_training.lower().strip()

    if dog_t == req_t:
        return sc["exact_match"]
    if dog_t in order and req_t in order:
        dist = abs(order.index(dog_t) - order.index(req_t))
        return max(sc["min_score"], sc["exact_match"] - dist * sc["penalty_per_step"])
    return sc["unknown"]


def score_age_compatibility(dog_age: Optional[str], requested_age: Optional[str]) -> float:
    sc = load_matching_config()["soft_rules"]["age_compatibility"]["scoring"]
    if not requested_age or not dog_age:
        return sc["unknown"]
    return sc["default"]


def score_kids_compatibility(dog_with_kids: Optional[bool], has_young_kids: bool) -> float:
    sc = load_matching_config()["soft_rules"]["kids_compatibility"]["scoring"]
    if dog_with_kids is None:
        return sc["unknown"]
    if not has_young_kids:
        return sc["no_young_kids_present"]
    return sc["friendly_with_kids"] if dog_with_kids else sc["not_friendly_with_kids"]


def score_pets_compatibility(
    dog_with_dogs: Optional[bool],
    dog_with_cats: Optional[bool],
    has_other_pets: bool,
    which_pets: str,
) -> float:
    sc = load_matching_config()["soft_rules"]["pets_compatibility"]["scoring"]
    if not has_other_pets:
        return sc["no_other_pets"]

    if dog_with_dogs is None and dog_with_cats is None:
        return sc["unknown"]

    which_pets_lower = which_pets.lower()
    score = 0.0
    if "dog" in which_pets_lower and dog_with_dogs:
        score += sc["per_pet_type"]
    if "cat" in which_pets_lower and dog_with_cats:
        score += sc["per_pet_type"]

    return score if score > 0 else sc["incompatible"]


def score_home_requirements(
    dog_size: Optional[str],
    has_house: Optional[bool],
    has_yard: Optional[bool],
) -> float:
    sc = load_matching_config()["soft_rules"]["home_requirements"]["scoring"]
    if has_house is None or has_yard is None:
        return sc["unknown"]

    size = (dog_size or "").lower().strip()

    if size == "large":
        tier = sc["large_dog"]
    elif size == "medium":
        tier = sc["medium_dog"]
    elif size == "small":
        tier = sc["small_dog"]
    else:
        return sc["unknown"]

    if has_house and has_yard:
        return tier["house_and_yard"]
    if has_house:
        return tier["house_only"]
    return tier["apartment"]


def calculate_soft_scores(dog: Dict, adoption_request: Dict) -> Dict[str, float]:
    """Calculate all soft matching scores."""
    cfg = load_matching_config()

    threshold = cfg["hard_rules"]["kids_compatibility"]["young_kids_age_threshold"]
    has_young_kids = adoption_request.get("has_kids") is True and not _has_only_older_kids(
        adoption_request.get("kids_age", ""), threshold
    )

    scores: Dict[str, float] = {}
    soft_rules = cfg["soft_rules"]

    if soft_rules["gender"]["enabled"]:
        scores["gender"] = score_gender(
            dog.get("gender"), adoption_request.get("requested_gender")
        )
    if soft_rules["size"]["enabled"]:
        scores["size"] = score_size(
            dog.get("size"), adoption_request.get("requested_size")
        )
    if soft_rules["energy_level"]["enabled"]:
        scores["energy_level"] = score_energy_level(
            dog.get("level_of_training"),  # used as energy proxy
            adoption_request.get("requested_level_energy"),
        )
    if soft_rules["training_level"]["enabled"]:
        scores["training_level"] = score_training_level(
            dog.get("level_of_training"),
            adoption_request.get("requested_level_of_train"),
        )
    if soft_rules["age_compatibility"]["enabled"]:
        scores["age_compatibility"] = score_age_compatibility(
            dog.get("age"), adoption_request.get("requested_age")
        )
    if soft_rules["kids_compatibility"]["enabled"]:
        scores["kids_compatibility"] = score_kids_compatibility(
            dog.get("get_along_with_kids"), has_young_kids
        )
    if soft_rules["pets_compatibility"]["enabled"]:
        scores["pets_compatibility"] = score_pets_compatibility(
            dog.get("get_along_with_dogs"),
            dog.get("get_along_with_cats"),
            adoption_request.get("has_other_pets", False),
            adoption_request.get("which_pets", ""),
        )
    if soft_rules["home_requirements"]["enabled"]:
        scores["home_requirements"] = score_home_requirements(
            dog.get("size"),
            adoption_request.get("has_house"),
            adoption_request.get("has_yard"),
        )

    return scores


def _weighted_average(scores: Dict[str, float], soft_rules: Dict) -> float:
    """Compute weighted average of soft scores using per-rule weights."""
    total_weight = 0.0
    weighted_sum = 0.0
    for name, score in scores.items():
        weight = soft_rules.get(name, {}).get("weight", 1.0)
        weighted_sum += score * weight
        total_weight += weight
    return (weighted_sum / total_weight) * 100 if total_weight > 0 else 0.0


# ============================================================
# PART 3: LLM-BASED CHARACTER MATCHING  (two-step pipeline)
# ============================================================

# ------------------------------------------------------------------
# Step 1 – Feature extraction
# ------------------------------------------------------------------

def _schema_placeholder(fields: List[str]) -> str:
    """Build a compact JSON schema string from a list of field names."""
    return json.dumps({f: "..." for f in fields}, indent=4)


def build_feature_extraction_prompt(dog: Dict, adoption_request: Dict, step_cfg: Dict) -> str:
    dog_fields = step_cfg["dog_features"]
    person_fields = step_cfg["person_features"]

    return f"""You are a pet adoption specialist. Extract structured features from the profiles below.

=== DOG PROFILE ===
Name        : {dog.get('name', 'Unknown')}
Breed       : {dog.get('breed', 'Unknown')}
Age         : {dog.get('age', 'Unknown')}
Size        : {dog.get('size', 'Unknown')}
Description : {dog.get('description', 'No description')}
Personality : {dog.get('happy_to', 'Not specified')}
Afraid of   : {dog.get('scared_of', 'Not specified')}

=== ADOPTER PROFILE ===
Why adopt        : {adoption_request.get('why_adopt', 'Not specified')}
Living situation : {adoption_request.get('dog_living_location', 'Not specified')}
House / Yard     : {adoption_request.get('has_house')} / {adoption_request.get('has_yard')}
Primary caregiver: {adoption_request.get('primary_care_giver', 'Not specified')}
Kids             : {adoption_request.get('has_kids')} (ages: {adoption_request.get('kids_age', 'N/A')})
Other pets       : {adoption_request.get('has_other_pets')} ({adoption_request.get('which_pets', 'N/A')})

Return ONLY valid JSON with this exact structure:
{{
    "dog_features": {_schema_placeholder(dog_fields)},
    "person_features": {_schema_placeholder(person_fields)}
}}"""


def extract_features(
    dog: Dict, adoption_request: Dict, llm_client, step_cfg: Dict
) -> Tuple[Dict, Dict]:
    """Call the LLM once to extract features for both dog and person."""
    prompt = build_feature_extraction_prompt(dog, adoption_request, step_cfg)
    raw = llm_client.extract(prompt)
    dog_features = raw.get("dog_features", {})
    person_features = raw.get("person_features", {})
    return dog_features, person_features


# ------------------------------------------------------------------
# Step 2 – Similarity scoring
# ------------------------------------------------------------------

def build_similarity_scoring_prompt(
    dog_features: Dict, person_features: Dict, step_cfg: Dict
) -> str:
    output_fields = step_cfg["output_fields"]
    output_schema = {
        "compatibility_score": "<integer 0-100>",
        "feature_matches": [
            {"feature": "<name>", "dog_value": "...", "person_value": "...", "match_quality": "excellent|good|fair|poor"}
        ],
        "key_strengths": ["..."],
        "potential_concerns": ["..."],
        "reasoning": "<overall explanation>",
        "recommendation": "<actionable recommendation>",
    }
    # Only keep keys the config requests
    output_schema = {k: v for k, v in output_schema.items() if k in output_fields}

    return f"""You are a pet adoption specialist. Score the compatibility between a dog and an adopter
based on the extracted features below.

=== DOG FEATURES ===
{json.dumps(dog_features, indent=2)}

=== PERSON FEATURES ===
{json.dumps(person_features, indent=2)}

For each feature that appears in both profiles, compare the values and assess how well they align.
Then produce an overall compatibility score.

Return ONLY valid JSON with this exact structure:
{json.dumps(output_schema, indent=4)}"""


def score_similarity(
    dog_features: Dict, person_features: Dict, llm_client, step_cfg: Dict, fallback_score: int
) -> Dict:
    """Call the LLM to produce a similarity score from the two feature dicts."""
    prompt = build_similarity_scoring_prompt(dog_features, person_features, step_cfg)
    raw = llm_client.extract(prompt)
    return {
        "compatibility_score": raw.get("compatibility_score", fallback_score),
        "feature_matches": raw.get("feature_matches", []),
        "key_strengths": raw.get("key_strengths", []),
        "potential_concerns": raw.get("potential_concerns", []),
        "reasoning": raw.get("reasoning", ""),
        "recommendation": raw.get("recommendation", ""),
    }


# ------------------------------------------------------------------
# Orchestrator
# ------------------------------------------------------------------

def get_llm_character_match(dog: Dict, adoption_request: Dict, llm_provider: str = "gemini") -> Dict:
    """
    Two-step LLM pipeline:
      1. Extract structured features for both dog and person.
      2. Score similarity based on those features.

    Returns a dict that includes the extracted features alongside the score,
    so callers can inspect what the model reasoned about.
    """
    llm_cfg = load_matching_config()["llm_analysis"]
    fallback_score = llm_cfg["fallback_score"]
    steps = llm_cfg["steps"]

    dog_features: Dict = {}
    person_features: Dict = {}
    similarity: Dict = {
        "compatibility_score": fallback_score,
        "feature_matches": [],
        "key_strengths": [],
        "potential_concerns": [],
        "reasoning": "LLM analysis unavailable",
        "recommendation": "Manual review recommended",
    }

    try:
        llm_client = get_llm_client(provider=llm_provider)

        # Step 1 – feature extraction
        if steps["feature_extraction"]["enabled"]:
            dog_features, person_features = extract_features(
                dog, adoption_request, llm_client, steps["feature_extraction"]
            )

        # Step 2 – similarity scoring
        if steps["similarity_scoring"]["enabled"]:
            similarity = score_similarity(
                dog_features, person_features, llm_client,
                steps["similarity_scoring"], fallback_score
            )

    except Exception as e:
        print(f"LLM error: {e}")
        similarity["potential_concerns"] = [f"Could not analyze with LLM: {str(e)}"]

    return {
        # Step 1 outputs – visible for inspection / debugging
        "dog_features": dog_features,
        "person_features": person_features,
        # Step 2 outputs
        **similarity,
    }


# ============================================================
# PART 4: COMBINED MATCHING SCORE
# ============================================================

def calculate_match_score_v2(
    dog: Dict,
    adoption_request: Dict,
    use_llm: bool = True,
    llm_provider: str = "gemini",
) -> Dict:
    """
    Calculate comprehensive match score combining:
    1. Hard filters (pass/fail)
    2. Soft scores (weighted)
    3. LLM character analysis
    """
    cfg = load_matching_config()
    weights = cfg["final_score"]

    passes_filters, rejection_reason = check_hard_filters(dog, adoption_request)

    result: Dict = {
        "passes_filters": passes_filters,
        "filter_rejection_reason": rejection_reason,
    }

    if not passes_filters:
        result.update(
            soft_score=0.0,
            soft_scores_breakdown={},
            character_match={
                "compatibility_score": 0,
                "key_strengths": [],
                "potential_concerns": [rejection_reason],
                "reasoning": f"Disqualified: {rejection_reason}",
                "recommendation": "Not recommended",
            },
            final_score=0.0,
            final_reasoning=rejection_reason,
        )
        return result

    soft_scores = calculate_soft_scores(dog, adoption_request)
    soft_score_avg = _weighted_average(soft_scores, cfg["soft_rules"])

    result["soft_score"] = round(soft_score_avg, 2)
    result["soft_scores_breakdown"] = {k: round(v * 100, 2) for k, v in soft_scores.items()}

    llm_enabled = cfg["llm_analysis"]["enabled"]
    if use_llm and llm_enabled:
        character_match = get_llm_character_match(dog, adoption_request, llm_provider)
    else:
        character_match = {
            "compatibility_score": soft_score_avg,
            "key_strengths": [],
            "potential_concerns": [],
            "reasoning": "LLM analysis disabled",
            "recommendation": "",
        }

    result["character_match"] = character_match

    final_score = (
        soft_score_avg * weights["soft_weight"]
        + character_match.get("compatibility_score", 50) * weights["llm_weight"]
    )
    result["final_score"] = round(final_score, 2)
    result["final_reasoning"] = " | ".join([
        f"Soft matching score: {result['soft_score']}%",
        f"Character compatibility: {character_match.get('compatibility_score', 50)}%",
        f"LLM analysis: {character_match.get('reasoning', '')}",
    ])

    return result
