import hashlib
import re


def make_fingerprint(rec):
    """Books: source + title. Quotes: source + author + first 50 chars of the quote."""
    if rec["source"] == "Books to Scrape":
        key = f'{rec["source"]} {rec["name_or_title"]}'
    else:
        key = f'{rec["source"]} {rec.get("author") or ""} {rec["name_or_title"][:50]}'
    key = re.sub(r"[^\w\s]", "", key.lower())
    key = " ".join(key.split())
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def find_duplicates(records):
    """Returns (unique, duplicates). The first copy is kept, later copies are dropped."""
    seen, unique, dupes = set(), [], []
    for rec in records:
        fp = make_fingerprint(rec)
        (dupes if fp in seen else unique).append(rec)
        seen.add(fp)
    return unique, dupes
