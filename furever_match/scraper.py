import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

_BASE = "https://herzelialovesanimals.org"
_CATEGORY_URL = f"{_BASE}/category/dogs/"

# Dog profile URLs look like /dog123/, /dog129-2/, /135-2/
_DOG_URL = re.compile(r"https://herzelialovesanimals\.org/(dog\d+[\w-]*|\d+-\d+)/?$", re.I)


def get_dog_profile_urls(category_url: str = _CATEGORY_URL) -> List[str]:
    """
    Scrapes all dog profile URLs from the category page.
    Matches URL patterns: /dog<number>/ or /<number>-<number>/
    """
    response = requests.get(category_url, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    dog_urls: set = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].rstrip("/") + "/"  # normalise trailing slash
        if _DOG_URL.match(href):
            dog_urls.add(href)

    return list(dog_urls)


def scrape_dog_page(dog_url: str) -> Dict:
    """
    Fetches an individual dog profile page and returns:
      - text: article body text (Hebrew), stripped of nav/footer noise
      - images: list of image URLs found in the article content
      - external_id: URL slug (e.g. "135-2" from /135-2/)
      - url: the original URL
    """
    response = requests.get(dog_url, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    # Target the article content area; fall back to <body> if not found
    content = (
        soup.find("div", class_=re.compile(r"entry[-_]content|post[-_]content", re.I))
        or soup.find("article")
        or soup.body
    )

    # Extract clean text
    for tag in content(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = content.get_text(separator=" ", strip=True)

    # Extract image URLs from the content area
    images = []
    for img in content.find_all("img", src=True):
        src = img["src"]
        if src.startswith("http"):
            images.append(src)
        elif src.startswith("/"):
            images.append(urljoin(_BASE, src))

    # Derive external_id from the URL path slug (last non-empty segment)
    path_parts = [p for p in urlparse(dog_url).path.split("/") if p]
    external_id = path_parts[-1] if path_parts else dog_url

    return {
        "text": text,
        "images": images,
        "external_id": external_id,
        "url": dog_url,
    }


def scrape_dog_description(dog_url: str) -> Optional[str]:
    """Legacy helper used by the scorer demo in main.py."""
    try:
        page = scrape_dog_page(dog_url)
        return page["text"]
    except Exception as e:
        print(f"Error scraping {dog_url}: {e}")
        return None
