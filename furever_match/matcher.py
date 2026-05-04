import json
from typing import List

from furever_match.db_ingestion import supabase
from furever_match.llm import LLMClient

_MATCH_PROMPT = """אתה מומחה להתאמת כלבים לאנשים שרוצים לאמץ.

להלן בקשת האימוץ של המועמד:
{request_summary}

להלן רשימת הכלבים הזמינים שעברו סינון ראשוני:
{dogs_list}

המשימה שלך:
- בחר את 3 הכלבים המתאימים ביותר למועמד
- דרג אותם מהמתאים ביותר לפחות מתאים
- לכל כלב תן ציון 0-100 והסבר קצר בעברית (2-3 משפטים) מדוע הוא מתאים

החזר JSON בלבד, ללא טקסט נוסף, בפורמט הבא:
[
  {{"dog_id": "...", "name": "...", "score": 85, "explanation": "..."}},
  {{"dog_id": "...", "name": "...", "score": 72, "explanation": "..."}},
  {{"dog_id": "...", "name": "...", "score": 60, "explanation": "..."}}
]
"""


def fetch_adoption_request(request_id: str) -> dict:
    result = (
        supabase.table("adoption_requests")
        .select("*")
        .eq("id", request_id)
        .single()
        .execute()
    )
    return result.data


def filter_dogs(request_id: str) -> List[dict]:
    """
    Step 1: Query dogs table with hard filters derived from the adoption request.
    Returns all matching available dogs.
    """
    request = fetch_adoption_request(request_id)

    query = supabase.table("dogs").select("*").eq("status", "available")

    if request.get("requested_gender"):
        query = query.eq("gender", request["requested_gender"])

    if request.get("requested_size"):
        query = query.eq("size", request["requested_size"])

    if request.get("requested_level_of_train"):
        query = query.eq("level_of_training", request["requested_level_of_train"])

    if request.get("has_kids"):
        query = query.eq("get_along_with_kids", True)

    if request.get("has_other_pets") and request.get("which_pets"):
        pets = request["which_pets"].lower()
        if "cat" in pets or "חתול" in pets:
            query = query.eq("get_along_with_cats", True)
        if "dog" in pets or "כלב" in pets:
            query = query.eq("get_along_with_dogs", True)

    result = query.execute()
    return result.data or []


def _format_request(request: dict) -> str:
    lines = []
    if request.get("why_adopt"):
        lines.append(f"סיבת האימוץ: {request['why_adopt']}")
    if request.get("has_kids"):
        lines.append(f"יש ילדים בבית (גיל: {request.get('kids_age', 'לא צוין')})")
    if request.get("has_other_pets"):
        lines.append(f"יש חיות מחמד אחרות: {request.get('which_pets', 'לא צוין')}")
    if request.get("has_yard"):
        lines.append("יש חצר")
    if request.get("has_house"):
        lines.append("גרים בבית פרטי")
    if request.get("requested_size"):
        lines.append(f"גודל מועדף: {request['requested_size']}")
    if request.get("requested_gender"):
        lines.append(f"מין מועדף: {request['requested_gender']}")
    if request.get("requested_level_energy"):
        lines.append(f"רמת אנרגיה מועדפת: {request['requested_level_energy']}")
    if request.get("requested_level_of_train"):
        lines.append(f"רמת אילוף מועדפת: {request['requested_level_of_train']}")
    if request.get("dog_living_location"):
        lines.append(f"הכלב יגור: {request['dog_living_location']}")
    return "\n".join(lines)


def _format_dogs(dogs: List[dict]) -> str:
    lines = []
    for i, dog in enumerate(dogs, 1):
        parts = [f"{i}. {dog.get('name', '?')} (id: {dog['id']})"]
        if dog.get("age"):
            parts.append(f"גיל: {dog['age']}")
        if dog.get("size"):
            parts.append(f"גודל: {dog['size']}")
        if dog.get("gender"):
            parts.append(f"מין: {dog['gender']}")
        if dog.get("level_of_training"):
            parts.append(f"אילוף: {dog['level_of_training']}")
        if dog.get("get_along_with_kids") is not None:
            parts.append(f"עם ילדים: {'כן' if dog['get_along_with_kids'] else 'לא'}")
        if dog.get("get_along_with_cats") is not None:
            parts.append(f"עם חתולים: {'כן' if dog['get_along_with_cats'] else 'לא'}")
        if dog.get("scared_of"):
            parts.append(f"מפחד מ: {dog['scared_of']}")
        if dog.get("description"):
            parts.append(f"תיאור: {dog['description']}")
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def llm_match(dogs: List[dict], adoption_request: dict, llm: LLMClient) -> List[dict]:
    """
    Step 2: Ask the LLM to pick and rank the top 3 dogs from the filtered list.
    Returns a list of up to 3 MatchResult dicts sorted by score descending.
    """
    prompt = _MATCH_PROMPT.format(
        request_summary=_format_request(adoption_request),
        dogs_list=_format_dogs(dogs),
    )
    results = llm.extract(prompt)
    if isinstance(results, list):
        return sorted(results, key=lambda r: r.get("score", 0), reverse=True)[:3]
    return []


def match(request_id: str, llm: LLMClient) -> List[dict]:
    """
    Full two-step match: DB filter → LLM ranking.
    Returns top 3 MatchResult dicts for the given adoption request.
    """
    dogs = filter_dogs(request_id)
    print(f"Step 1: {len(dogs)} dogs passed the filter.")
    if not dogs:
        print("No dogs matched the hard filters.")
        return []

    request = fetch_adoption_request(request_id)
    print("Step 2: Sending to LLM for ranking...")
    return llm_match(dogs, request, llm)
