"""
Run: uv run python pipeline.py --limit=20
"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv

from furever_match.db_ingestion import ingest_dog
from furever_match.extractor import extract_raw_dog_data
from furever_match.llm import get_llm_client
from furever_match.scraper import get_dog_profile_urls, scrape_dog_page

load_dotenv()

_CATEGORY_URL = "https://herzelialovesanimals.org/category/dogs/"


def run_pipeline(limit: int = None) -> None:
    provider = os.getenv("LLM_PROVIDER", "ollama")
    llm = get_llm_client(provider)

    print(f"Using LLM provider: {provider}")
    print(f"Scraping dog URLs from {_CATEGORY_URL} ...")
    urls = sorted(get_dog_profile_urls(_CATEGORY_URL))
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
            print(f"  Error: {e}")


if __name__ == "__main__":
    limit = None
    for arg in sys.argv[1:]:
        if arg.startswith("--limit="):
            limit = int(arg.split("=")[1])
    run_pipeline(limit=limit)
