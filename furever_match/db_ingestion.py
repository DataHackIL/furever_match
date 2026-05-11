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

_HE = {
    # which_pets
    'cat':        'חתול',
    'dog':        'כלב',
    'cat,dog':    'חתול וכלב',
    # morning_wakeup
    'early':      'לפני 7:00',
    'normal':     '7:00–8:00',
    'late':       'אחרי 8:00',
    # morning_walk / noon_walk / evening_walk
    'short':      'קצר',
    'medium':     'בינוני',
    'long':       'ארוך',
    'run':        'ריצה ארוכה',
    'none':       'ללא',
    # walk_who
    'me':         'אני',
    'adult':      'מבוגר אחר',
    'kids':       'ילדים',
    'na':         'לא רלוונטי',
    # morning_play
    'daily':      'יומי',
    'sometimes':  'לפעמים',
    'rarely':     'לעיתים רחוקות',
    # where_lives
    'inside':     'בבית',
    'garden':     'גינה',
    'both':       'שניהם',
    # work_situation
    'wfh':        'עבודה מהבית',
    'office':     'משרד — הכלב לבד',
    'arranged':   'פתרון מסודר',
    # work_alone_hours
    '0':          'אפס שעות',
    '1-4':        'עד 4 שעות',
    '4+':         '4 שעות+',
    # work_lunch
    'no':         'לא',
    # evening_sleep
    'bed':        'איתי במיטה',
    'own-bed':    'מיטה משלו',
    'living-room':'סלון',
    # evening_quality
    'couch':      'ספה ביחד',
    'play':       'משחק פעיל',
    'training':   'אילוף',
    # weekend_outing
    'local':      'אזור מגורים',
    'nature':     'טבע ופארקים',
    'variety':    'חופים וערים',
    # weekend_intensity
    'relaxed':    'מרגוע',
    'high':       'גבוה — ריצות / טיולים',
    # weekend_sport
    'running':    'ריצה / רכיבה',
    'water':      'שחייה / אג\'יליטי',
}


def _he(value):
    if not value:
        return None
    return _HE.get(str(value).strip(), str(value).strip()) or None


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
        "external_id": raw.get("external_id")
    }


def transform_adoption_request(raw):
    return {
        "why_adopt": clean_text(raw.get("why_adopt")),

        "has_kids": normalize_yes_no(raw.get("has_kids")),
        "kids_age": clean_text(raw.get("kids_age")),

        "has_other_pets": normalize_yes_no(raw.get("has_other_pets")),
        "which_pets": _he(raw.get("which_pets")),

        "has_yard": normalize_yes_no(raw.get("has_yard")),
        "has_house": normalize_yes_no(raw.get("has_house")),

        "requested_level_of_train": clean_text(raw.get("requested_level_of_train")),
        "requested_gender": normalize_gender(raw.get("requested_gender")),
        "requested_age": clean_text(raw.get("requested_age")),
        "requested_size": normalize_size(raw.get("requested_size")),
        "requested_level_energy": normalize_energy_level(raw.get("requested_level_energy")),

        "dog_living_location": clean_text(raw.get("dog_living_location")),
        "primary_care_giver": clean_text(raw.get("primary_care_giver")),

        # Day-in-life fields (stored in Hebrew)
        "morning_wakeup": _he(raw.get("morning_wakeup")),
        "morning_walk": _he(raw.get("morning_walk")),
        "morning_walk_who": _he(raw.get("morning_walk_who")),
        "morning_play": _he(raw.get("morning_play")),
        "where_lives": _he(raw.get("where_lives")),
        "work_situation": _he(raw.get("work_situation")),
        "work_alone_hours": _he(raw.get("work_alone_hours")),
        "work_lunch": _he(raw.get("work_lunch")),
        "noon_walk": _he(raw.get("noon_walk")),
        "noon_walk_who": _he(raw.get("noon_walk_who")),
        "evening_walk": _he(raw.get("evening_walk")),
        "evening_sleep": _he(raw.get("evening_sleep")),
        "evening_quality": _he(raw.get("evening_quality")),
        "weekend_outing": _he(raw.get("weekend_outing")),
        "weekend_intensity": _he(raw.get("weekend_intensity")),
        "weekend_sport": _he(raw.get("weekend_sport")),
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


