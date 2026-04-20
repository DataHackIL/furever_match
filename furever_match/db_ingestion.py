import os
from supabase import create_client
from dotenv import load_dotenv
import re

load_dotenv()

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

# -----------------------------
# Helpers (CLEANING LOGIC)
# -----------------------------

def clean_text(value):
    if not value:
        return None
    return str(value).strip()

def normalize_yes_no(value):
    if not value:
        return None
    v = str(value).strip().lower()
    if v in ["yes", "y", "true", "1", "כן"]:
        return True
    if v in ["no", "n", "false", "0", "לא"]:
        return False
    return None

def normalize_age(value):
    if not value:
        return None
    value = value.lower()

    # try to extract number of years/months
    years = re.search(r"(\d+)\s*year", value)
    months = re.search(r"(\d+)\s*month", value)

    if years:
        return f"{years.group(1)} years"
    if months:
        return f"{months.group(1)} months"

    return value.strip()

def normalize_size(value):
    if not value:
        return None
    v = value.lower()
    if "small" in v:
        return "small"
    if "medium" in v:
        return "medium"
    if "large" in v:
        return "large"
    return value.strip().lower()

def normalize_gender(value):
    if not value:
        return None
    v = value.lower()
    if "male" in v or "m" == v:
        return "male"
    if "female" in v or "f" == v:
        return "female"
    return None

def normalize_location(value):
    if not value:
        return None
    return value.split("area")[0].strip()


# -----------------------------
# MAIN TRANSFORM FUNCTION
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
        "external_id": raw.get("external_id")
    }


# -----------------------------
# INGESTION LOGIC
# -----------------------------

def ingest_dog(raw_dog):
    dog_data = transform_dog(raw_dog)

    # 1. insert into dogs table
    response = supabase.table("dogs").insert(dog_data).execute()

    if not response.data:
        print("Insert failed or duplicate:", dog_data["external_id"])
        return

    dog_id = response.data[0]["id"]

    # 2. insert images
    images = raw_dog.get("images", [])
    for url in images:
        if url:
            supabase.table("dog_images").insert({
                "dog_id": dog_id,
                "image_url": url
            }).execute()

    print(f"Inserted dog {dog_data['name']} with {len(images)} images")

