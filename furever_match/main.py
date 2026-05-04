import os
import sys

from dotenv import load_dotenv

from furever_match.db_ingestion import ingest_dog
from furever_match.extractor import extract_dog_profile, extract_raw_dog_data
from furever_match.llm import get_llm_client
from furever_match.matcher import match
from furever_match.models import UserPreferences
from furever_match.scorer import calculate_match_score
from furever_match.scraper import get_dog_profile_urls, scrape_dog_description, scrape_dog_page

load_dotenv()

_CATEGORY_URL = "https://herzelialovesanimals.org/category/dogs/"


def run_pipeline(category_url: str = _CATEGORY_URL, limit: int = None) -> None:
    """
    Full pipeline: scrape -> extract -> ingest.
    Reads LLM_PROVIDER (ollama|gemini) from environment.
    Skips dogs already in the database (duplicate external_id).
    limit: process only the first N dogs (useful for testing).
    """
    provider = os.getenv("LLM_PROVIDER", "ollama")
    llm = get_llm_client(provider)

    print(f"Using LLM provider: {provider}")
    print(f"Scraping dog URLs from {category_url} ...")
    urls = sorted(get_dog_profile_urls(category_url))
    if limit:
        urls = urls[:limit]
    print(f"Processing {len(urls)} dog profiles.\n")

    for url in urls:
        print(f"Processing: {url}")
        try:
            page = scrape_dog_page(url)
            raw = extract_raw_dog_data(page["text"], llm)
            raw["source"] = "herzelialovesanimals.org"
            raw["external_id"] = page["external_id"]
            raw["images"] = page["images"]
            ingest_dog(raw)
        except Exception as e:
            print(f"  Error processing {url}: {e}")


def main() -> None:
    """Scorer demo: scrape one dog, extract a DogProfile, calculate match score."""
    user = UserPreferences(
        has_cat=False,
        ideal_energy_level=3,
        ideal_size=2,
    )
    print(f"User Preferences: {user}\n")

    print("Scraping dog URLs from herzelialovesanimals.org...")
    dog_urls = get_dog_profile_urls()
    print(f"Found {len(dog_urls)} dog profiles.\n")

    if not dog_urls:
        print("No dogs found. Maybe the website structure changed?")
        return

    demo_url = dog_urls[0]
    print(f"Scraping description for: {demo_url}")
    description = scrape_dog_description(demo_url)

    if not description:
        print("Could not extract description.")
        return

    print(f"Extracted Description excerpt: {description[:100]}...\n")

    print("Sending to local Ollama (gemma4:26b) for DogProfile extraction...")
    try:
        dog_profile = extract_dog_profile(description_he=description)
        print("\n--- Extracted Dog Profile ---")
        print(f"Name: {dog_profile.name}")
        print(f"Breed: {dog_profile.breed}")
        print(f"Age: {dog_profile.age_group}")
        print(f"Energy (1-5): {dog_profile.energy_level}")
        print(f"Size (1-5): {dog_profile.size}")
        print(f"Cat Friendly: {dog_profile.cat_friendly}")
        print("-----------------------------\n")

        score = calculate_match_score(dog=dog_profile, user=user)
        print(f"MATCH SCORE FOR THIS USER: {score * 100:.1f}%")

    except Exception as e:
        print(f"Error during extraction or scoring: {e}")


if __name__ == "__main__":
    if "--pipeline" in sys.argv:
        limit = None
        for arg in sys.argv:
            if arg.startswith("--limit="):
                limit = int(arg.split("=")[1])
        run_pipeline(limit=limit)
    elif any(a.startswith("--match=") for a in sys.argv):
        request_id = next(a.split("=")[1] for a in sys.argv if a.startswith("--match="))
        llm = get_llm_client(os.getenv("LLM_PROVIDER", "ollama"))
        results = match(request_id, llm)
        print(f"\nTop {len(results)} matches:\n")
        for r in results:
            print(f"  {r.get('score', '?'):>3}/100  {r.get('name', '?')}")
            print(f"         {r.get('explanation', '')}")
            print()
    else:
        main()
