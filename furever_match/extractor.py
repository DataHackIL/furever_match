from furever_match.llm import LLMClient

_RAW_PROMPT = """You are an expert at extracting structured information from Hebrew pet-adoption posts.

Extract the dog's details from the text below and return a JSON object with EXACTLY these keys:

{{
  "name": string or null,
  "breed": string or null,
  "age": string (e.g. "2 years", "6 months") or null,
  "size": "small" | "medium" | "large" | null,
  "gender": "male" | "female" | null,
  "description": string (1-2 sentence summary in Hebrew) or null,
  "location": string or null,
  "get_along_with_cats": true | false | null,
  "get_along_with_dogs": true | false | null,
  "get_along_with_kids": true | false | null,
  "scared_of": string or null,
  "happy_to": string or null,
  "level_of_training": "low" | "medium" | "high" | null
}}

Rules:
- Use null when information is not mentioned — do not guess.
- gender: ♂ or "זכר" or "הוא" = "male". ♀ or "נקבה" or "היא" = "female". If not clear, use null.
- size: small = up to ~10 kg, medium = 10-25 kg, large = over 25 kg.
- Keep description in Hebrew.
- Respond ONLY with a valid JSON object. No markdown, no explanation.

Text:
{text}
"""


def extract_raw_dog_data(text: str, llm: LLMClient) -> dict:
    prompt = _RAW_PROMPT.format(text=text[:4000])
    return llm.extract(prompt)
