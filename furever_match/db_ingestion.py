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
    if value is None:
        return None
    value = str(value).strip().lower()
    if not value:
        return None

    years = re.search(r"(\d+)\s*(?:year|שנ)", value)
    months = re.search(r"(\d+)\s*(?:month|חוד)", value)

    if years:
        return f"{years.group(1)} years"
    if months:
        return f"{months.group(1)} months"

    # bare integer — assume years
    if re.fullmatch(r"\d+", value):
        return f"{value} years"

    # decimal fraction of a year (e.g. 0.6) — convert to months
    decimal = re.fullmatch(r"0\.(\d+)", value)
    if decimal:
        months = round(float(value) * 12)
        return f"{months} months"

    return value

def normalize_size(value):
    if not value:
        return None
    v = value.lower()
    if "small" in v or "קטן" in v:
        return "small"
    if "medium" in v or "בינוני" in v:
        return "medium"
    if "large" in v or "גדול" in v:
        return "large"
    return value.strip().lower()

def normalize_gender(value):
    if not value:
        return None
    v = value.lower().strip()
    if v in ("male", "m") or "זכר" in v:
        return "male"
    if v in ("female", "f") or "נקבה" in v:
        return "female"
    # "לא משנה" (no preference) and anything else → no preference
    return None

def normalize_location(value):
    if not value:
        return None
    return value.split("area")[0].strip()

def normalize_energy_level(value):
    if not value:
        return None
    v = value.lower().strip()
    if v in ("low", "נמוכה", "נמוך"):
        return "low"
    if v in ("medium", "בינונית", "בינוני"):
        return "medium"
    if v in ("high", "גבוהה", "גבוה"):
        return "high"
    if v in ("very_high", "very high", "גבוה מאוד", "אינסופי"):
        return "very_high"
    return None


def normalize_which_pets(value):
    if not value:
        return None
    v = value.lower().strip()
    has_cat = "cat" in v or "חתול" in v
    has_dog = "dog" in v or "כלב" in v
    if has_cat and has_dog:
        return "cat,dog"
    if has_cat:
        return "cat"
    if has_dog:
        return "dog"
    return clean_text(value)


def normalize_age_category(value):
    if not value:
        return None
    v = str(value).strip().lower()
    if v in ("puppy", "gur", "גור"):
        return "puppy"
    if v in ("young", "junior", "צעיר"):
        return "young"
    if v in ("adult", "mature", "בוגר"):
        return "adult"
    if v in ("senior", "old", "older", "elderly", "מבוגר", "ותיק", "זקן"):
        return "senior"
    return None


def normalize_training_level(value):
    if not value:
        return None
    v = value.strip()
    vl = v.lower()
    if vl in ("beginner", "מתחיל"):
        return "beginner"
    if vl in ("basic", "בסיסי"):
        return "basic"
    if vl in ("intermediate", "בינוני"):
        return "intermediate"
    if vl in ("advanced", "מתקדם"):
        return "advanced"
    if vl in ("professional", "מקצועי"):
        return "professional"
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
        "external_id": raw.get("external_id")
    }


def transform_adoption_request(raw):
    return {
        "why_adopt": clean_text(raw.get("why_adopt")),

        "has_kids": normalize_yes_no(raw.get("has_kids")),
        "kids_age": clean_text(raw.get("kids_age")),

        "has_other_pets": normalize_yes_no(raw.get("has_other_pets")),
        "which_pets": normalize_which_pets(raw.get("which_pets")),

        "has_yard": normalize_yes_no(raw.get("has_yard")),
        "has_house": normalize_yes_no(raw.get("has_house")),

        "requested_level_of_train": normalize_training_level(raw.get("requested_level_of_train")),
        "requested_gender": normalize_gender(raw.get("requested_gender")),
        "requested_age": normalize_age_category(raw.get("requested_age")),
        "requested_size": normalize_size(raw.get("requested_size")),
        "requested_level_energy": normalize_energy_level(raw.get("requested_level_energy")),

        "dog_living_location": clean_text(raw.get("dog_living_location")),
        "primary_care_giver": clean_text(raw.get("primary_care_giver")),

        # Day-in-life fields (stored as English keys; translated to Hebrew at API layer)
        "morning_wakeup": clean_text(raw.get("morning_wakeup")),
        "morning_walk": clean_text(raw.get("morning_walk")),
        "morning_walk_who": clean_text(raw.get("morning_walk_who")),
        "morning_play": clean_text(raw.get("morning_play")),
        "where_lives": clean_text(raw.get("where_lives")),
        "work_situation": clean_text(raw.get("work_situation")),
        "work_alone_hours": clean_text(raw.get("work_alone_hours")),
        "work_lunch": clean_text(raw.get("work_lunch")),
        "noon_walk": clean_text(raw.get("noon_walk")),
        "noon_walk_who": clean_text(raw.get("noon_walk_who")),
        "evening_walk": clean_text(raw.get("evening_walk")),
        "evening_sleep": clean_text(raw.get("evening_sleep")),
        "evening_quality": clean_text(raw.get("evening_quality")),
        "weekend_outing": clean_text(raw.get("weekend_outing")),
        "weekend_intensity": clean_text(raw.get("weekend_intensity")),
        "weekend_sport": clean_text(raw.get("weekend_sport")),
    }


# -----------------------------
# INGESTION LOGIC
# -----------------------------

def ingest_dog(raw_dog):
    dog_data = transform_dog(raw_dog)

    # skip if already in DB
    existing = supabase.table("dogs").select("id").eq("external_id", dog_data["external_id"]).execute()
    if existing.data:
        print(f"  Skipping {dog_data['name']} (already in DB)")
        return

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


