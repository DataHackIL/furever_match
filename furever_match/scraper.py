import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

_DOG_URL_PATTERN = re.compile(
    r"https://herzelialovesanimals\.org/([a-z][\w-]*\d[\w-]*|\d[\w-]*)/?$"
)
_CATEGORY_URL = "https://herzelialovesanimals.org/category/dogs/"


def get_dog_profile_urls(category_url: str = _CATEGORY_URL) -> list:
    resp = httpx.get(category_url, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    seen = set()
    urls = []
    for a in soup.find_all("a", href=True):
        href = a["href"].rstrip("/")
        if _DOG_URL_PATTERN.match(href + "/") or _DOG_URL_PATTERN.match(href):
            if href not in seen:
                seen.add(href)
                urls.append(href)
    return urls


def scrape_dog_page(url: str) -> dict:
    resp = httpx.get(url, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    content = soup.find(class_="entry-content") or soup.find("article") or soup.body
    text = content.get_text(separator="\n", strip=True) if content else ""

    images = []
    if content:
        for img in content.find_all("img", src=True):
            src = img["src"]
            if any(ext in src.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                images.append(src)

    slug = urlparse(url).path.strip("/").split("/")[-1]
    return {"text": text, "images": images, "external_id": slug, "url": url}


def scrape_dog_description(url: str) -> str:
    page = scrape_dog_page(url)
    return page["text"]
