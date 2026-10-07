"""Small pure functions: a value goes in, a cleaned value comes out. No internet, no files."""
import re
from urllib.parse import urlparse

RATING_MAP = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
BOOKS = "Books to Scrape"
QUOTES = "Quotes to Scrape"


def clean_text(value):
    if value is None:
        return None
    text = " ".join(str(value).replace("\xa0", " ").split())
    return text or None


def strip_quotes(value):
    text = clean_text(value)
    if text is None:
        return None
    return clean_text(text.strip("\u201c\u201d\"'"))


def clean_price(raw):
    if not raw:
        return None
    match = re.search(r"\d+(?:\.\d+)?", str(raw).replace(",", ""))
    return float(match.group()) if match else None


def clean_rating(raw):
    for word in (raw or "").lower().split():
        if word in RATING_MAP:
            return RATING_MAP[word]
    return None


def clean_tags(tags):
    cleaned = {clean_text(t).lower() for t in (tags or []) if clean_text(t)}
    return ";".join(sorted(cleaned)) or None


def normalize_url(url):
    url = clean_text(url)
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return url


def clean_book(raw, scraped_at):
    return {
        "source": BOOKS,
        "source_url": normalize_url(raw.get("url")),
        "name_or_title": clean_text(raw.get("title")),
        "category": clean_text(raw.get("category")),
        "price": clean_price(raw.get("price_raw")),
        "rating": clean_rating(raw.get("rating_raw")),
        "author": None,
        "tags": None,
        "description": clean_text(raw.get("description")),
        "scraped_at": scraped_at,
    }


def clean_quote(raw, scraped_at):
    return {
        "source": QUOTES,
        "source_url": normalize_url(raw.get("page_url")),
        "name_or_title": strip_quotes(raw.get("text")),
        "category": "Quotes",
        "price": None,
        "rating": None,
        "author": clean_text(raw.get("author")),
        "tags": clean_tags(raw.get("tags")),
        "description": None,
        "scraped_at": scraped_at,
    }
