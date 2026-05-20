"""
Single source of truth for all English <-> Hebrew translations.

Internal storage is always English.
Call `translate_value(value)` or `translate_record(record, fields)` when
building API responses that the Hebrew UI will consume.
"""
from typing import Optional

# ---------------------------------------------------------------------------
# English → Hebrew display values
# ---------------------------------------------------------------------------

EN_TO_HE: dict = {
    # age categories
    "puppy":        "גור",
    "young":        "צעיר",
    "adult":        "בוגר",
    "senior":       "מבוגר",

    # energy (very_high added for runner profile)
    "very_high":    "גבוה מאוד",

    # gender
    "male":         "זכר",
    "female":       "נקבה",

    # size
    "small":        "קטן",
    "medium":       "בינוני",
    "large":        "גדול",

    # energy level
    "low":          "נמוך",
    "high":         "גבוה",

    # training level (3 levels)
    "basic":        "בסיסי",
    "intermediate": "בינוני",
    "advanced":     "מתקדם",

    # pets
    "cat":          "חתול",
    "dog":          "כלב",
    "cat,dog":      "חתול וכלב",

    # morning wakeup
    "early":        "לפני 7:00",
    "normal":       "7:00-8:00",
    "late":         "אחרי 8:00",

    # walk length
    "short":        "קצר",
    "long":         "ארוך",
    "run":          "ריצה ארוכה",
    "none":         "ללא",

    # walk who
    "me":           "אני",
    "adult":        "מבוגר אחר",
    "kids":         "ילדים",
    "na":           "לא רלוונטי",

    # morning play
    "daily":        "יומי",
    "sometimes":    "לפעמים",
    "rarely":       "לעיתים רחוקות",

    # where dog lives
    "inside":       "בבית",
    "garden":       "גינה",
    "both":         "שניהם",

    # work situation
    "wfh":          "עבודה מהבית",
    "office":       "משרד - הכלב לבד",
    "arranged":     "פתרון מסודר",

    # work alone hours
    "0":            "אפס שעות",
    "1-4":          "עד 4 שעות",
    "4+":           "4 שעות+",

    # work lunch
    "no":           "לא",

    # evening sleep
    "bed":          "איתי במיטה",
    "own-bed":      "מיטה משלו",
    "living-room":  "סלון",

    # evening quality
    "couch":        "ספה ביחד",
    "play":         "משחק פעיל",
    "training":     "אילוף",

    # weekend outing
    "local":        "אזור מגורים",
    "nature":       "טבע ופארקים",
    "variety":      "חופים וערים",

    # weekend intensity
    "relaxed":      "מרגוע",

    # weekend sport
    "running":      "ריצה / רכיבה",
    "water":        "שחייה / אגיליטי",
}

# Build reverse map for normalising Hebrew → English at ingestion time
HE_TO_EN: dict = {v: k for k, v in EN_TO_HE.items()}

# ---------------------------------------------------------------------------
# Fields that should be translated in outgoing API responses
# ---------------------------------------------------------------------------

TRANSLATABLE_DOG_FIELDS = [
    "size", "gender", "level_of_training",
]

TRANSLATABLE_REQUEST_FIELDS = [
    "requested_gender", "requested_size",
    "requested_level_energy", "requested_level_of_train",
    "requested_age", "which_pets",
    "where_lives", "work_alone_hours",
    "morning_walk", "morning_walk_who",
    "noon_walk", "noon_walk_who",
    "evening_walk", "evening_walk_who",
]

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def translate_value(value: Optional[str]) -> Optional[str]:
    """Translate a single English enum value to Hebrew. Returns original if unknown."""
    if value is None:
        return None
    return EN_TO_HE.get(str(value).lower().strip(), value)


def normalize_to_english(value: Optional[str]) -> Optional[str]:
    """Convert a Hebrew (or already-English) value to the canonical English key."""
    if value is None:
        return None
    v = str(value).strip()
    # already English?
    if v.lower() in EN_TO_HE:
        return v.lower()
    # try Hebrew lookup
    return HE_TO_EN.get(v)


def translate_record(record: dict, fields: list) -> dict:
    """Return a copy of record with the specified fields translated to Hebrew."""
    out = dict(record)
    for field in fields:
        if field in out:
            out[field] = translate_value(out[field])
    return out


def translate_dog(dog: dict) -> dict:
    return translate_record(dog, TRANSLATABLE_DOG_FIELDS)


def translate_adoption_request(req: dict) -> dict:
    return translate_record(req, TRANSLATABLE_REQUEST_FIELDS)
