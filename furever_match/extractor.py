import json
from furever_match.llm import LLMClient, OllamaClient
from furever_match.models import DogProfile

_RAW_PROMPT = """You are an expert at extracting structured information from Hebrew pet-adoption posts.

Extract the dog's details from the text below and return a JSON object with EXACTLY these keys:

{{
  "name": string or null,
  "breed": string or null,
  "age": string (e.g. "2 years", "6 months") or null,
  "size": "small" | "medium" | "large" | null,
  "gender": "male" | "female" | null,
  "description": string (1-2 sentence summary in the original language, Hebrew) or null,
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
- size: small = up to ~10 kg, medium = 10-25 kg, large = over 25 kg.
- Respond ONLY with a valid JSON object. No markdown, no explanation.

Text:
{text}
"""

_PROFILE_PROMPT = """You are an expert at extracting structured information from text.
Extract the dog's profile details from the following Hebrew description.

Rules:
- name: String, the dog's name.
- breed: String, the dog's breed.
- age_group: String, MUST be one of: 'puppy', 'adult', 'senior'
- energy_level: Integer, from 1 to 5
- size: Integer, from 1 to 5
- cat_friendly: Boolean. True if good with cats, false if bad, infer from context.
- is_neutralized: Boolean. True if spayed/neutered.
- compatibility_score: Dictionary mapping categories like 'kids', 'other_dogs' to scores (1-5).

Hebrew Description:
{description}

Respond ONLY with a valid JSON object. Do not wrap in markdown tags like ```json.
"""


def extract_raw_dog_data(text: str, llm: LLMClient) -> dict:
    """
    Uses the provided LLMClient to extract structured ingestion fields from page text.
    Returns a plain dict with keys matching RawDogData (minus source/external_id/images).
    """
    prompt = _RAW_PROMPT.format(text=text[:4000])
    return llm.extract(prompt)


def extract_dog_profile(
    description_he: str,
    model_name: str = "gemma3:4b",
    llm: LLMClient = None,
) -> DogProfile:
    """
    Extracts a DogProfile (used by the scorer demo in main.py).
    Pass an LLMClient to override; otherwise defaults to OllamaClient with model_name.
    """
    client = llm or OllamaClient(model=model_name)
    prompt = _PROFILE_PROMPT.format(description=description_he)
    data = client.extract(prompt)
    return DogProfile(**data)
