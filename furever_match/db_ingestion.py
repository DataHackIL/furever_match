import os
import re

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)


# -----------------------------
# Helpers (CLEANING LOGIC)
# -----------------------------

def clean_text(value):
    if not value:
        return None
    return str(value).strip()


def normalize_yes_no(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    v = str(value).strip().lower()
    if v in ["yes", "y", "true", "1", "כן"]:
        return True
    if v in ["no", "n", "false", "0", "לא"]:
        return False
    return None


def normalize_age(value):
    if not value:
        return None
    v = value.lower()

    years = re.search(r"(\d+)\s*(year|שנה|שנים|שנתיים)", v)
    months = re.search(r"(\d+)\s*(month|חודש|חודשים)", v)

    if years:
        n = years.group(1)
        return f"{n} year" if n == "1" else f"{n} years"
    if months:
        n = months.group(1)
        return f"{n} month" if n == "1" else f"{n} months"

    # Hebrew words without digits
    if "שנתיים" in v:
        return "2 years"
    if re.search(r"שנה|שנים", v):
        return v.strip()

    return v.strip()


def normalize_size(value):
    if not value:
        return None
    v = value.lower()
    if v in ("small", "קטן", "קטנה") or "small" in v:
        return "small"
    if v in ("medium", "בינוני", "בינונית") or "medium" in v:
        return "medium"
    if v in ("large", "גדול", "גדולה") or "large" in v:
        return "large"
    return None


def normalize_gender(value):
    if not value:
        return None
    v = value.lower()
    if "male" in v or v == "m" or "זכר" in v:
        return "male"
    if "female" in v or v == "f" or "נקבה" in v:
        return "female"
    return None


def normalize_location(value):
    if not value:
        return None
    return value.split("area")[0].strip()

def normalize_energy_level(value):
    if not value:
        return None
    v = value.lower().strip()
    if "low" in v:
        return "low"
    if "medium" in v:
        return "medium"
    if "high" in v:
        return "high"
    return None


# -----------------------------
# MAIN TRANSFORM FUNCTIONS
# -----------------------------

def transform_dog(raw):
    return {
        "name": clean_text(raw.get("name")),
        "breed": clean_text(raw.get("breed")),
        "age": normalize_age(raw.get("age")),
        "size": normalize_size(raw.get("size")),
        "gender": normalize_gender(raw.get("gender")),
        "description": clean_text(raw.get("description")),
        "location": normalize_location(raw.get("location")),

        "get_along_with_cats": normalize_yes_no(raw.get("get_along_with_cats")),
        "get_along_with_dogs": normalize_yes_no(raw.get("get_along_with_dogs")),
        "get_along_with_kids": normalize_yes_no(raw.get("get_along_with_kids")),

        "scared_of": clean_text(raw.get("scared_of")),
        "happy_to": clean_text(raw.get("happy_to")),
        "level_of_training": clean_text(raw.get("level_of_training")),

        "status": "available",
        "source": raw.get("source"),
        "external_id": raw.get("external_id"),
    }


def transform_adoption_request(raw):
    return {
        "why_adopt": clean_text(raw.get("why_adopt")),

        "has_kids": normalize_yes_no(raw.get("has_kids")),
        "kids_age": clean_text(raw.get("kids_age")),

        "has_other_pets": normalize_yes_no(raw.get("has_other_pets")),
        "which_pets": clean_text(raw.get("which_pets")),

        "has_yard": normalize_yes_no(raw.get("has_yard")),
        "has_house": normalize_yes_no(raw.get("has_house")),

        "requested_level_of_train": clean_text(raw.get("requested_level_of_train")),
        "requested_gender": normalize_gender(raw.get("requested_gender")),
        "requested_age": clean_text(raw.get("requested_age")),
        "requested_size": normalize_size(raw.get("requested_size")),
        "requested_level_energy": normalize_energy_level(raw.get("requested_level_energy")),

        "dog_living_location": clean_text(raw.get("dog_living_location")),
        "primary_care_giver": clean_text(raw.get("primary_care_giver"))
    }


# -----------------------------
# INGESTION LOGIC
# -----------------------------

def ingest_dog(raw_dog):
    dog_data = transform_dog(raw_dog)
    external_id = dog_data.get("external_id")

    # Skip duplicates
    if external_id:
        existing = (
            supabase.table("dogs")
            .select("id")
            .eq("external_id", external_id)
            .execute()
        )
        if existing.data:
            print(f"Skipping duplicate: {external_id}")
            return

    response = supabase.table("dogs").insert(dog_data).execute()

    if not response.data:
        print(f"Insert failed for: {external_id}")
        return

    dog_id = response.data[0]["id"]

    images = raw_dog.get("images", [])
    for url in images:
        if url:
            supabase.table("dog_images").insert({
                "dog_id": dog_id,
                "image_url": url,
            }).execute()

    print(f"Inserted '{dog_data['name']}' ({external_id}) with {len(images)} images")


def ingest_adoption_request(raw_request):
    request_data = transform_adoption_request(raw_request)

    # insert into adoption_requests table
    response = supabase.table("adoption_requests").insert(request_data).execute()

    if not response.data:
        print("Failed to insert adoption request")
        return

    request_id = response.data[0]["id"]
    print(f"Inserted adoption request {request_id}")
    return request_id
