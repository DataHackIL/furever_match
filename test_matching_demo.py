"""
Matching demo: 3 adopter profiles x real dogs from the database.
Shows per-rule scores and top-3 candidates per person.
Results are printed to console AND saved to matching_results.txt.

Run with:  python test_matching_demo.py
"""

import sys, io
from datetime import datetime

# UTF-8 console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from furever_match.db_ingestion import supabase
from furever_match.matching_v2 import (
    calculate_match_score_v2, check_filter_dominance,
    _has_only_older_kids, load_matching_config,
    extract_person_features,
)
from furever_match.matching_integration_v2 import _build_character_match
from furever_match.llm import get_llm_client
import furever_match.matching_v2 as mv2

mv2._config_cache = None

RESULTS_FILE = "matching_results.txt"
USE_LLM = True   # set True to run Gemini analysis on top-3 candidates

# -----------------------------------------------------------------------
# Derive labels from matching_rules.yaml — never hardcode rule names
# -----------------------------------------------------------------------

def _rule_label(key: str) -> str:
    """Turn a snake_case rule key into a padded display label."""
    return key.replace("_", " ").title().ljust(15)

def _build_labels():
    cfg = load_matching_config()
    hard = {k: _rule_label(k) for k in cfg["hard_rules"]}
    soft = {k: _rule_label(k) for k in cfg["soft_rules"]}
    return hard, soft

HARD_LABELS, SOFT_LABELS = _build_labels()

# -----------------------------------------------------------------------
# Tee: write to both console and file simultaneously
# -----------------------------------------------------------------------

_file_out = open(RESULTS_FILE, "w", encoding="utf-8")

def _print(*args, **kwargs):
    print(*args, **kwargs)
    print(*args, **{k: v for k, v in kwargs.items() if k != "file"}, file=_file_out)

# -----------------------------------------------------------------------
# 3 Adopter profiles
# -----------------------------------------------------------------------

ADOPTERS = [
    {
        "_label": "Young Urban Professional",
        "_description": "Single, apartment, no kids, no pets — wants a calm small companion",
        "why_adopt": "Looking for a relaxed companion for apartment living",
        "has_kids": False,
        "kids_age": None,
        "has_other_pets": False,
        "which_pets": None,
        "has_house": False,
        "has_yard": False,
        "requested_gender": None,
        "requested_size": "small",
        "requested_level_energy": "low",
        "requested_level_of_train": "basic",
        "requested_age": "adult",
        "dog_living_location": "apartment",
        "primary_care_giver": "me",
    },
    {
        "_label": "Family with Young Children",
        "_description": "House + yard, kids aged 5 & 7, no other pets — wants young large dog, 3 walks/day",
        "why_adopt": "מחפשת כלב שישחק עם הילדים ויהיה חבר שלהם",
        "has_kids": True,
        "kids_age": "5,7",
        "has_other_pets": False,
        "which_pets": None,
        "has_house": True,
        "has_yard": True,
        "requested_gender": None,
        "requested_size": "large",
        "requested_level_energy": "medium",
        "requested_level_of_train": "intermediate",
        "requested_age": "young",
        "dog_living_location": "house with yard",
        "primary_care_giver": "both parents",
        "morning_walk": "medium",
        "morning_walk_who": "me",
        "noon_walk": "medium",
        "noon_walk_who": "adult",
        "evening_walk": "medium",
        "evening_walk_who": "me",
        "work_alone_hours": "4+",
    },
    {
        "_label": "Elderly Companion Seeker",
        "_description": "Older adult, apartment, has cat, wants calm adult medium dog, walks 3×/day",
        "why_adopt": "אני מבוגרת ומחפשת כלב רגוע שיפיג את הבדידות",
        "has_kids": False,
        "kids_age": None,
        "has_other_pets": False,
        "which_pets": None,
        "has_house": False,
        "has_yard": False,
        "requested_gender": None,
        "requested_size": "medium",
        "requested_level_energy": "low",
        "requested_level_of_train": "intermediate",
        "requested_age": "adult",
        "dog_living_location": "apartment",
        "primary_care_giver": "me",
        "morning_walk": "medium",
        "morning_walk_who": "me",
        "noon_walk": "medium",
        "noon_walk_who": "me",
        "evening_walk": "medium",
        "evening_walk_who": "me",
        "work_alone_hours": "4+",
    },
    {
        "_label": "Active Outdoor Enthusiast",
        "_description": "Apartment, no kids, no pets — wants a high-energy male medium dog",
        "why_adopt": "I hike and run daily and want an active dog to join me",
        "has_kids": False,
        "kids_age": None,
        "has_other_pets": False,
        "which_pets": None,
        "has_house": False,
        "has_yard": False,
        "requested_gender": "male",
        "requested_size": "medium",
        "requested_level_energy": "high",
        "requested_level_of_train": "intermediate",
        "requested_age": None,
        "dog_living_location": "apartment",
        "primary_care_giver": "me",
    },
]

# -----------------------------------------------------------------------
# Formatting helpers
# -----------------------------------------------------------------------

def _bar(pct: float, width: int = 10) -> str:
    filled = round(pct / 100 * width)
    return "#" * filled + "." * (width - filled)

def _fmt_score(pct: float) -> str:
    return f"[{_bar(pct)}]  {pct:5.1f}%"


# -----------------------------------------------------------------------
# Per-rule hard filter detail (mirrors check_hard_filters logic)
# -----------------------------------------------------------------------

def _hard_rule_details(dog: dict, adopter: dict) -> list:
    """Evaluate each hard rule from the config and return (label, passed, note)."""
    cfg = load_matching_config()["hard_rules"]
    results = []

    for rule_key, rule in cfg.items():
        if not rule.get("enabled", True):
            continue
        label = HARD_LABELS.get(rule_key, _rule_label(rule_key))

        if rule_key == "gender":
            req = adopter.get(rule.get("person_field", "requested_gender"))
            val = dog.get(rule.get("dog_field", "gender"))
            if req:
                passed = not (val and val.lower() != req.lower())
                note = f"dog={val or '?'}  wanted={req}"
            else:
                passed, note = True, "no preference"

        elif rule_key == "pets_compatibility":
            has_pets = adopter.get("has_other_pets") is True
            if has_pets:
                which = (adopter.get("which_pets") or "").lower()
                fail = None
                for check in rule.get("checks", {}).values():
                    if check["trigger_contains"] in which and dog.get(check["dog_field"]) is False:
                        fail = check["rejection_message"]
                        break
                passed = fail is None
                note = which or "no pets"
            else:
                passed, note = True, "no other pets"

        elif rule_key == "kids_compatibility":
            has_kids = adopter.get("has_kids") is True
            if has_kids:
                threshold = rule.get("young_kids_age_threshold", 16)
                has_young = not _has_only_older_kids(adopter.get("kids_age") or "", threshold)
                if has_young:
                    passed = dog.get(rule.get("dog_field", "get_along_with_kids")) is not False
                    note = f"ages {adopter.get('kids_age')}  (young if <={threshold})"
                else:
                    passed, note = True, f"all kids >{threshold} — treated as adults"
            else:
                passed, note = True, "no kids"

        else:
            # Generic field-equality check for any future hard rules
            req = adopter.get(rule.get("person_field", ""))
            val = dog.get(rule.get("dog_field", ""))
            if req:
                passed = not (val and str(val).lower() != str(req).lower())
                note = f"dog={val or '?'}  wanted={req}"
            else:
                passed, note = True, "no preference"

        results.append((label, passed, note))

    return results

# -----------------------------------------------------------------------
# Print one candidate
# -----------------------------------------------------------------------

def _print_candidate(rank: int, dog: dict, match: dict, adopter: dict) -> None:
    from furever_match.matching_v2 import _infer_dog_energy
    name     = dog.get("name", "Unknown")
    breed    = dog.get("breed", "?")
    size     = dog.get("size", "?")
    gender   = dog.get("gender", "?")
    age      = dog.get("age", "?")
    training = dog.get("level_of_training", "?")
    energy   = dog.get("energy_level") or f"{_infer_dog_energy(dog)} (inferred)"

    _print(f"\n  {'-'*62}")
    _print(f"  #{rank}  {name}  ({breed})")
    _print(f"      {gender} | {size} | age: {age} | training: {training} | energy: {energy}")
    _print(f"  {'-'*62}")

    _print("  HARD FILTERS:")
    for label, passed, note in _hard_rule_details(dog, adopter):
        icon = "+" if passed else "!"
        _print(f"    {icon} {label}  {note}")

    _print("\n  SOFT SCORES:")
    breakdown = match.get("soft_scores_breakdown", {})
    for key, label in SOFT_LABELS.items():
        score = breakdown.get(key)
        if score is not None:
            _print(f"    {label}  {_fmt_score(score)}")
        else:
            _print(f"    {label}  -- (not scored)")

    _print(f"\n  OVERALL SCORE:  {match['final_score']:.1f}%"
           f"  (soft {match['soft_score']:.1f}%)")

    cm = match.get("character_match", {})
    _print(f"\n  PERSONALITY MATCH:")
    if not USE_LLM:
        _print(f"    (disabled — set USE_LLM=True to enable)")
    else:
        _print(f"    Compatibility score: {cm.get('compatibility_score', '?')}%")
        strengths = cm.get("key_strengths") or []
        concerns  = cm.get("potential_concerns") or []
        reasoning = cm.get("reasoning", "")
        recommendation = cm.get("recommendation", "")
        if strengths:
            _print(f"    Strengths:")
            for s in strengths:
                _print(f"      + {s}")
        if concerns:
            _print(f"    Concerns:")
            for c in concerns:
                _print(f"      ! {c}")
        if reasoning:
            _print(f"    Reasoning: {reasoning}")
        if recommendation:
            _print(f"    Recommendation: {recommendation}")

# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def run_demo():
    _print(f"FurEver Match — Matching Demo")
    _print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    _print("=" * 64)

    _print("\nFetching available dogs from database...")
    try:
        dogs = supabase.table("dogs").select("*").eq("status", "available").execute().data or []
    except Exception as e:
        _print(f"  DB error: {e}")
        dogs = []

    if not dogs:
        _print("  No dogs found. Aborting.")
        return

    _print(f"  Found {len(dogs)} available dog(s).\n")

    for adopter in ADOPTERS:
        _print("\n" + "=" * 64)
        _print(f"  ADOPTER: {adopter['_label']}")
        _print(f"  {adopter['_description']}")
        _print("=" * 64)

        scored = []
        for dog in dogs:
            m = calculate_match_score_v2(dog, adopter, use_llm=False)
            scored.append((dog, m))

        scored.sort(key=lambda x: (not x[1]["passes_filters"], -x[1]["final_score"]))
        passed = [(d, m) for d, m in scored if m["passes_filters"]]
        failed = [(d, m) for d, m in scored if not m["passes_filters"]]

        # Check for over-restrictive filters
        warnings = check_filter_dominance(dogs, adopter)
        if warnings:
            _print(f"\n  *** FILTER WARNINGS ***")
            for w in warnings:
                _print(f"  [!] {w['message']}")
            _print("")

        top3 = passed[:3]
        if not top3:
            _print("\n  No dogs passed all hard filters for this adopter.")
            _print(f"  Rejected ({len(failed)}):")
            for dog, m in failed[:5]:
                _print(f"    ! {dog.get('name','?')} ({dog.get('breed','?')}) -- {m['filter_rejection_reason']}")
            continue

        _print(f"\n  Top {len(top3)} match(es)  ({len(passed)} passed, {len(failed)} rejected)")

        # Personality matching: 1 LLM call (person features) + local comparison per dog
        if USE_LLM:
            _print("  Extracting person features (1 LLM call)...")
            cfg = load_matching_config()
            person_features = {}
            try:
                llm_client = get_llm_client(provider=cfg["llm_analysis"].get("default_provider", "ollama"))
                person_features = extract_person_features(adopter, llm_client, cfg["llm_analysis"]["steps"]["feature_extraction"])
            except Exception as e:
                _print(f"  [WARN] Person feature extraction failed: {e}")

            top3_ids = [dog["id"] for dog, _ in top3]
            dog_features_map = {}
            try:
                rows = supabase.table("dog_llm_features").select("dog_id, features").in_("dog_id", top3_ids).execute().data or []
                dog_features_map = {r["dog_id"]: r["features"] for r in rows}
            except Exception as e:
                _print(f"  [WARN] Could not load pre-computed dog features: {e}")

            weights = cfg["final_score"]
            enriched = []
            for dog, m in top3:
                precomputed = dog_features_map.get(dog["id"])
                cm = _build_character_match(precomputed, person_features, m["soft_score"])
                final = m["soft_score"] * weights["soft_weight"] + cm["compatibility_score"] * weights["llm_weight"]
                m = dict(m, character_match=cm, final_score=round(final, 2))
                enriched.append((dog, m))
            top3 = enriched

        for rank, (dog, m) in enumerate(top3, 1):
            _print_candidate(rank, dog, m, adopter)

        if failed:
            _print(f"\n  Rejected ({len(failed)} dog(s)):")
            for dog, m in failed:
                _print(f"    ! {dog.get('name','?')} ({dog.get('breed','?')}) -- {m['filter_rejection_reason']}")

    _print("\n" + "=" * 64)
    _print("  Demo complete.")
    _print("=" * 64)

    _file_out.close()
    print(f"\n  Results saved to: {RESULTS_FILE}", file=sys.stdout)


if __name__ == "__main__":
    run_demo()
