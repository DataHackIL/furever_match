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
import re
import yaml
from typing import Dict, List, Tuple, Optional
from furever_match.llm import get_llm_client
from furever_match.db_ingestion import (
    normalize_gender, normalize_size,
    normalize_energy_level, normalize_training_level,
    normalize_which_pets, normalize_age_category,
)

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
# NORMALISATION HELPERS
# ============================================================

# Maps training vocabulary → energy vocabulary for the energy scoring rule.
# A dog's training level is a reliable proxy for its energy/activity needs.
_TRAINING_TO_ENERGY: Dict[str, str] = {
    "beginner":     "low",
    "basic":        "low",
    "intermediate": "medium",
    "advanced":     "high",
    "professional": "very_high",
}


def _norm_dog(dog: Dict) -> Dict:
    """Return a copy of dog with enum fields normalised to English using field-specific rules."""
    out = dict(dog)
    if out.get("size"):
        out["size"] = normalize_size(out["size"]) or out["size"]
    if out.get("gender"):
        out["gender"] = normalize_gender(out["gender"]) or out["gender"]
    if out.get("level_of_training"):
        # Normalise to training vocabulary (beginner→professional)
        out["level_of_training"] = normalize_training_level(out["level_of_training"]) or out["level_of_training"]
    return out


def _norm_request(req: Dict) -> Dict:
    """Return a copy of adoption_request with enum fields normalised to English."""
    out = dict(req)
    # normalize_gender returns None for no-preference ("לא משנה") — that's correct
    out["requested_gender"] = normalize_gender(out.get("requested_gender"))
    if out.get("requested_size"):
        out["requested_size"] = normalize_size(out["requested_size"]) or out["requested_size"]
    if out.get("requested_level_energy"):
        out["requested_level_energy"] = normalize_energy_level(out["requested_level_energy"]) or out["requested_level_energy"]
    if out.get("requested_level_of_train"):
        out["requested_level_of_train"] = normalize_training_level(out["requested_level_of_train"]) or out["requested_level_of_train"]
    if out.get("which_pets"):
        out["which_pets"] = normalize_which_pets(out["which_pets"]) or out["which_pets"]
    if out.get("requested_age"):
        out["requested_age"] = normalize_age_category(out["requested_age"]) or out["requested_age"]
    return out


# ============================================================
# PART 1: HARD FILTERS (Disqualifying Factors)
# ============================================================

def check_hard_filters(dog: Dict, adoption_request: Dict) -> Tuple[bool, Optional[str]]:
    """
    Apply hard filters that completely disqualify a dog.
    Returns: (passes_filters: bool, reason_if_rejected: str or None)
    """
    dog = _norm_dog(dog)
    adoption_request = _norm_request(adoption_request)
    cfg = load_matching_config()["hard_rules"]

    # --- gender ---
    gc = cfg["gender"]
    if gc["enabled"]:
        requested_gender = adoption_request.get(gc["person_field"])
        if requested_gender:
            dog_gender = dog.get(gc["dog_field"])
            if dog_gender and dog_gender.lower() != requested_gender.lower():
                return False, gc["rejection_message"]

    # --- size ---
    sc = cfg["size"]
    if sc["enabled"]:
        requested_size = adoption_request.get(sc["person_field"])
        if requested_size:
            dog_size = dog.get(sc["dog_field"])
            if dog_size and dog_size.lower() != requested_size.lower():
                return False, sc["rejection_message"]

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

    return True, None


def check_filter_dominance(dogs: List[Dict], adoption_request: Dict) -> List[Dict]:
    """
    Test each hard rule independently against the full dog pool.
    Returns a list of warning dicts for any rule that eliminates more than
    the configured threshold of dogs on its own.
    """
    cfg = load_matching_config()
    fw = cfg.get("filter_warnings", {})
    if not fw.get("enabled", True) or not dogs:
        return []

    threshold = fw.get("threshold", 0.95)
    messages  = fw.get("messages", {})
    total     = len(dogs)
    req       = _norm_request(adoption_request)
    warnings  = []

    def _warn(rule: str, value: str, eliminated: int) -> None:
        pct_elim = eliminated / total
        if pct_elim < threshold:
            return
        pct_kept = round((1 - pct_elim) * 100, 1)
        tmpl = messages.get(rule, "Your {rule} preference eliminates too many dogs.")
        warnings.append({
            "rule": rule,
            "preference": value,
            "pct_eliminated": round(pct_elim * 100, 1),
            "pct_kept": pct_kept,
            "message": tmpl.format(rule=rule, value=value, pct_kept=pct_kept),
        })

    hard = cfg["hard_rules"]

    # gender
    gc = hard["gender"]
    if gc["enabled"]:
        req_g = req.get(gc["person_field"])
        if req_g:
            eliminated = sum(
                1 for dog in dogs
                if (g := _norm_dog(dog).get(gc["dog_field"])) and g.lower() != req_g.lower()
            )
            _warn("gender", req_g, eliminated)

    # size
    sc = hard["size"]
    if sc["enabled"]:
        req_s = req.get(sc["person_field"])
        if req_s:
            eliminated = sum(
                1 for dog in dogs
                if (s := _norm_dog(dog).get(sc["dog_field"])) and s.lower() != req_s.lower()
            )
            _warn("size", req_s, eliminated)

    # pets_compatibility
    pc = hard["pets_compatibility"]
    if pc["enabled"] and req.get("has_other_pets") is True:
        which = (req.get("which_pets") or "").lower()
        eliminated = 0
        for dog in dogs:
            nd = _norm_dog(dog)
            for check in pc["checks"].values():
                if check["trigger_contains"] in which and nd.get(check["dog_field"]) is False:
                    eliminated += 1
                    break
        _warn("pets_compatibility", which, eliminated)

    # kids_compatibility
    kc = hard["kids_compatibility"]
    if kc["enabled"] and req.get("has_kids") is True:
        age_threshold = kc["young_kids_age_threshold"]
        has_young = not _has_only_older_kids(req.get("kids_age") or "", age_threshold)
        if has_young:
            eliminated = sum(1 for dog in dogs if dog.get(kc["dog_field"]) is False)
            _warn("kids_compatibility", "kids-friendly", eliminated)

    return warnings


def _has_only_older_kids(kids_age: str, threshold: int = 16) -> bool:
    """Return True only when all kids are above the threshold age (threshold itself is still young)."""
    if not kids_age:
        return False
    for age in kids_age.split(","):
        try:
            if int(age.strip()) <= threshold:
                return False
        except ValueError:
            pass
    return True


# ============================================================
# PART 2: SOFT SCORING (Matching Percentages)
# ============================================================

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


def _parse_age_years(age_str: str) -> Optional[float]:
    """Convert '3 years' or '6 months' to a float number of years."""
    if not age_str:
        return None
    s = age_str.lower().strip()
    m = re.search(r"(\d+(?:\.\d+)?)\s*year", s)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*month", s)
    if m:
        return float(m.group(1)) / 12
    try:
        return float(s)
    except ValueError:
        return None


_AGE_CATEGORY_MAP = {
    # English
    "puppy": "puppy", "gur": "puppy",
    "young": "young", "junior": "young",
    "adult": "adult", "mature": "adult",
    "senior": "senior", "old": "senior", "older": "senior", "elderly": "senior",
    # Hebrew
    "גור": "puppy",
    "צעיר": "young",
    "בוגר": "adult",
    "מבוגר": "senior", "ותיק": "senior", "זקן": "senior",
}


def _normalize_age_category(value: str) -> Optional[str]:
    """Map a free-text age preference to a canonical category."""
    if not value:
        return None
    return _AGE_CATEGORY_MAP.get(str(value).strip().lower())


def score_age_compatibility(dog_age: Optional[str], requested_age: Optional[str]) -> float:
    rule = load_matching_config()["soft_rules"]["age_compatibility"]
    sc = rule["scoring"]

    if not dog_age or not requested_age:
        return sc["unknown"]

    age_years = _parse_age_years(dog_age)
    if age_years is None:
        return sc["unknown"]

    # Bucket the dog's age
    dog_cat = None
    for cat, (lo, hi) in rule["categories"].items():
        if lo <= age_years < hi:
            dog_cat = cat
            break
    if not dog_cat:
        return sc["unknown"]

    req_cat = _normalize_age_category(requested_age)
    if not req_cat:
        return sc["unknown"]

    if dog_cat == req_cat:
        return sc["exact_match"]

    order = rule["category_order"]
    if dog_cat in order and req_cat in order:
        dist = abs(order.index(dog_cat) - order.index(req_cat))
        return max(sc["min_score"], sc["exact_match"] - dist * sc["penalty_per_step"])

    return sc["unknown"]


def score_home_requirements(
    dog_size: Optional[str],
    dog_energy: Optional[str],
    has_house: Optional[bool],
    has_yard: Optional[bool],
) -> float:
    """Score home fit using a combined matrix of dog size, energy level, and home type."""
    sc = load_matching_config()["soft_rules"]["home_requirements"]["scoring"]
    if has_house is None or has_yard is None:
        return sc["unknown"]

    size = (dog_size or "").lower().strip()
    energy = (dog_energy or "").lower().strip()

    size_key = {"large": "large_dog", "medium": "medium_dog", "small": "small_dog"}.get(size)
    energy_key = {"high": "high_energy", "medium": "medium_energy", "low": "low_energy"}.get(energy)

    if not size_key or not energy_key:
        return sc["unknown"]

    tier = sc[size_key][energy_key]
    if has_house and has_yard:
        return tier["house_and_yard"]
    if has_house:
        return tier["house_only"]
    return tier["apartment"]


def calculate_soft_scores(dog: Dict, adoption_request: Dict) -> Dict[str, float]:
    """Calculate all soft matching scores."""
    dog = _norm_dog(dog)
    adoption_request = _norm_request(adoption_request)
    cfg = load_matching_config()
    scores: Dict[str, float] = {}
    soft_rules = cfg["soft_rules"]

    if soft_rules["energy_level"]["enabled"]:
        training_val = dog.get("level_of_training")
        # Map training vocab → energy vocab for the energy scoring rule
        energy_proxy = _TRAINING_TO_ENERGY.get(training_val or "", training_val)
        scores["energy_level"] = score_energy_level(
            energy_proxy,
            adoption_request.get("requested_level_energy"),
        )
    if soft_rules["age_compatibility"]["enabled"]:
        scores["age_compatibility"] = score_age_compatibility(
            dog.get("age"), adoption_request.get("requested_age")
        )
    if soft_rules["training_level"]["enabled"]:
        scores["training_level"] = score_training_level(
            dog.get("level_of_training"),
            adoption_request.get("requested_level_of_train"),
        )
    if soft_rules["home_requirements"]["enabled"]:
        training_val2 = dog.get("level_of_training")
        energy_proxy2 = _TRAINING_TO_ENERGY.get(training_val2 or "", training_val2)
        scores["home_requirements"] = score_home_requirements(
            dog.get("size"),
            energy_proxy2,
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
