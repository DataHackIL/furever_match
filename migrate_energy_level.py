"""
Populate energy_level for all dogs in the database.

Pipeline per dog:
  1. LLM reads Hebrew description + breed + age → classifies low/medium/high/very_high
  2. Fallback (LLM unavailable or no description):
       - Base from age:  puppy/young → high,  adult → medium,  senior → low
       - Breed boost (+1 step) for energetic breeds:
         Belgian/German/Dutch Shepherd, Husky, Pit/Pitbull

Run:
    py migrate_energy_level.py

Add --dry-run to preview without writing to DB.
Add --llm to enable LLM classification (requires Ollama running or GEMINI_API_KEY).
"""

import sys, io, argparse, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from furever_match.db_ingestion import supabase
from furever_match.matching_v2 import load_matching_config

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ENERGY_ORDER = ["low", "medium", "high", "very_high"]

ENERGETIC_BREEDS = [
    "רועה בלגי", "רועה גרמני", "רועה הולנדי",
    "האסקי", "husky",
    "פיטבול", "פיט", "pitbull", "pit bull",
    "belgian", "german shepherd", "dutch shepherd",
]

LLM_PROMPT = """\
You are classifying a shelter dog's energy level based on its profile.
Return ONLY a JSON object with a single key "energy_level" whose value is
exactly one of: low, medium, high, very_high.

Rules:
- low:      calm, quiet, couch dog, shy/fearful (often sedentary)
- medium:   enjoys walks, playful but settles at home
- high:     energetic, loves long walks/runs, active breed needing exercise
- very_high: extremely energetic, needs intense daily exercise, working-dog drive

Dog profile:
  Name: {name}
  Breed: {breed}
  Age: {age}
  Description: {description}

Return only: {{"energy_level": "low"|"medium"|"high"|"very_high"}}
"""

# ---------------------------------------------------------------------------
# Rule-based fallback
# ---------------------------------------------------------------------------

def _parse_age_years(age_str: str) -> float:
    """Extract numeric age in years from strings like '3 years', '7 months'."""
    if not age_str:
        return None
    s = str(age_str).lower()
    m = re.search(r"(\d+(?:\.\d+)?)\s*(year|שנ|month|חוד)", s)
    if not m:
        n = re.search(r"(\d+(?:\.\d+)?)", s)
        return float(n.group(1)) if n else None
    val = float(m.group(1))
    unit = m.group(2)
    if "month" in unit or "חוד" in unit:
        val = val / 12.0
    return val


def _step(energy: str, delta: int) -> str:
    idx = ENERGY_ORDER.index(energy)
    return ENERGY_ORDER[max(0, min(len(ENERGY_ORDER) - 1, idx + delta))]


def rule_based_energy(dog: dict) -> str:
    age_years = _parse_age_years(dog.get("age") or "")
    breed = (dog.get("breed") or "").lower()

    # Age baseline
    if age_years is None:
        base = "medium"
    elif age_years < 1:
        base = "high"
    elif age_years < 4:
        base = "high"
    elif age_years < 7:
        base = "medium"
    else:
        base = "low"

    # Breed boost for energetic breeds
    is_energetic = any(b in breed for b in ENERGETIC_BREEDS)
    if is_energetic:
        base = _step(base, +1)

    return base


# ---------------------------------------------------------------------------
# LLM classification
# ---------------------------------------------------------------------------

def llm_energy(dog: dict, llm_client) -> str:
    prompt = LLM_PROMPT.format(
        name=dog.get("name", ""),
        breed=dog.get("breed", ""),
        age=dog.get("age", ""),
        description=dog.get("description", ""),
    )
    result = llm_client.extract(prompt)
    val = str(result.get("energy_level", "")).strip().lower()
    if val in ENERGY_ORDER:
        return val
    raise ValueError(f"unexpected energy_level value from LLM: {val!r}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no DB writes")
    parser.add_argument("--llm", action="store_true", help="Use LLM for classification")
    parser.add_argument("--overwrite", action="store_true", help="Re-classify dogs that already have energy_level")
    args = parser.parse_args()

    llm_client = None
    if args.llm:
        try:
            from furever_match.llm import get_llm_client
            cfg = load_matching_config()["llm_analysis"]
            provider = cfg.get("default_provider", "ollama")
            llm_client = get_llm_client(provider=provider)
            print(f"LLM provider: {provider}")
        except Exception as e:
            print(f"[WARN] LLM unavailable, using rule-based fallback: {e}")

    dogs = supabase.table("dogs").select("id, name, breed, age, energy_level, description").execute().data or []
    print(f"Found {len(dogs)} dogs.\n")

    updated = 0
    skipped = 0
    failed = 0

    for dog in dogs:
        name = dog.get("name", "?")
        existing = dog.get("energy_level")

        if existing and not args.overwrite:
            print(f"  SKIP  {name:12}  already has: {existing}")
            skipped += 1
            continue

        method = "rule"
        energy = None

        if llm_client and dog.get("description"):
            try:
                energy = llm_energy(dog, llm_client)
                method = "llm"
            except Exception as e:
                print(f"  [WARN] LLM failed for {name}: {e}")

        if energy is None:
            energy = rule_based_energy(dog)

        status = "DRY" if args.dry_run else "SET"
        print(f"  {status}   {name:12}  {energy:10}  ({method})  breed={dog.get('breed','?')}  age={dog.get('age','?')}")

        if not args.dry_run:
            try:
                supabase.table("dogs").update({"energy_level": energy}).eq("id", dog["id"]).execute()
                updated += 1
            except Exception as e:
                print(f"    [ERROR] DB write failed: {e}")
                failed += 1

    print(f"\nDone. updated={updated}  skipped={skipped}  failed={failed}")
    if args.dry_run:
        print("(dry run — no changes written)")


if __name__ == "__main__":
    main()
