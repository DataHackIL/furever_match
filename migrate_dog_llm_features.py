"""
Pre-compute LLM features for all dogs and store in dog_llm_features table.

Run once after creating the table, and again whenever new dogs are added.

    py migrate_dog_llm_features.py
    py migrate_dog_llm_features.py --overwrite   # re-compute all
    py migrate_dog_llm_features.py --dry-run     # preview only
    py migrate_dog_llm_features.py --provider gemini
"""

import sys, io, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from furever_match.db_ingestion import supabase
from furever_match.matching_v2 import extract_dog_features, load_matching_config
from furever_match.llm import get_llm_client


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",   action="store_true", help="Preview only, no DB writes")
    parser.add_argument("--overwrite", action="store_true", help="Re-compute dogs that already have features")
    parser.add_argument("--provider",  default=None,        help="LLM provider: ollama | gemini")
    args = parser.parse_args()

    cfg = load_matching_config()
    llm_cfg = cfg["llm_analysis"]
    provider = args.provider or llm_cfg.get("default_provider", "ollama")
    model = (
        llm_cfg["providers"].get(provider, {}).get("model")
        or (llm_cfg["providers"]["ollama"]["base_url"] and "llama3.2")
    )
    step_cfg = llm_cfg["steps"]["feature_extraction"]

    llm_client = get_llm_client(provider=provider)
    print(f"Provider: {provider}\n")

    dogs = supabase.table("dogs").select("id, name, breed, age, size, level_of_training, description, happy_to, scared_of").execute().data or []
    print(f"Found {len(dogs)} dogs.\n")

    existing = set()
    if not args.overwrite:
        rows = supabase.table("dog_llm_features").select("dog_id").execute().data or []
        existing = {r["dog_id"] for r in rows}

    updated = skipped = failed = 0

    for dog in dogs:
        name = dog.get("name", "?")
        if dog["id"] in existing:
            print(f"  SKIP  {name}")
            skipped += 1
            continue

        try:
            features = extract_dog_features(dog, llm_client, step_cfg)
            status = "DRY" if args.dry_run else "SET"
            print(f"  {status}   {name:15}  {list(features.keys())}")

            if not args.dry_run:
                supabase.table("dog_llm_features").upsert({
                    "dog_id":   dog["id"],
                    "features": features,
                    "model":    provider,
                }).execute()
                updated += 1

        except Exception as e:
            print(f"  [ERROR] {name}: {e}")
            failed += 1

    print(f"\nDone. updated={updated}  skipped={skipped}  failed={failed}")
    if args.dry_run:
        print("(dry run — no changes written)")


if __name__ == "__main__":
    main()
