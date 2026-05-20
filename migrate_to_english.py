"""
One-time migration: normalise all Hebrew enum values in Supabase to English.
Safe to re-run — only updates rows where a value needs changing.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from furever_match.db_ingestion import (
    supabase,
    normalize_gender, normalize_size, normalize_energy_level,
    normalize_training_level, normalize_which_pets,
)

# ---------------------------------------------------------------------------
# adoption_requests
# ---------------------------------------------------------------------------

print("=== Migrating adoption_requests ===")
rows = supabase.table("adoption_requests").select(
    "id,requested_gender,requested_size,requested_level_energy,"
    "requested_level_of_train,which_pets"
).execute().data or []

updated = 0
for row in rows:
    patch = {}

    new_gender = normalize_gender(row["requested_gender"])
    if new_gender != row["requested_gender"]:
        patch["requested_gender"] = new_gender

    new_size = normalize_size(row["requested_size"])
    if new_size != row["requested_size"]:
        patch["requested_size"] = new_size

    new_energy = normalize_energy_level(row["requested_level_energy"])
    if new_energy != row["requested_level_energy"]:
        patch["requested_level_energy"] = new_energy

    new_train = normalize_training_level(row["requested_level_of_train"])
    if new_train != row["requested_level_of_train"]:
        patch["requested_level_of_train"] = new_train

    new_pets = normalize_which_pets(row["which_pets"])
    if new_pets != row["which_pets"]:
        patch["which_pets"] = new_pets

    if patch:
        supabase.table("adoption_requests").update(patch).eq("id", row["id"]).execute()
        print(f"  updated request {row['id']}: {patch}")
        updated += 1

print(f"  {updated}/{len(rows)} adoption requests updated\n")

# ---------------------------------------------------------------------------
# dogs — fix level_of_training Hebrew/non-standard values
# ---------------------------------------------------------------------------

TRAINING_MAP = {
    "מדיום":                    "medium",
    "מחונך לבית ולצרכים":      "basic",
    "מחונך לצרכים":             "basic",
}

print("=== Migrating dogs ===")
dogs = supabase.table("dogs").select("id,level_of_training").execute().data or []

updated = 0
for dog in dogs:
    val = dog["level_of_training"]
    if val in TRAINING_MAP:
        new_val = TRAINING_MAP[val]
        supabase.table("dogs").update({"level_of_training": new_val}).eq("id", dog["id"]).execute()
        print(f"  updated dog {dog['id']}: level_of_training {val!r} -> {new_val!r}")
        updated += 1

print(f"  {updated}/{len(dogs)} dogs updated\n")
print("Migration complete.")
