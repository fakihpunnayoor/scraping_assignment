"""Run the whole pipeline:  python main.py"""
import argparse
import csv
import json
import logging
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from processing.cleaning import clean_book, clean_quote
from processing.deduplication import find_duplicates
from processing.validation import validate_record
from scrapers.base_scraper import create_session
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
LOG_FILE = BASE / "logs" / "scraper.log"
COLUMNS = ["source", "source_url", "name_or_title", "category", "price", "rating",
           "author", "tags", "description", "scraped_at"]

logger = logging.getLogger("main")


def setup_logging():
    LOG_FILE.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
                  logging.StreamHandler()],
    )


def process_source(name, scraper, cleaner, max_pages):
    """scrape -> clean -> validate -> deduplicate for one source."""
    stats = {"raw": 0, "cleaned": 0, "rejected": 0, "rejected_by_reason": {},
             "duplicates": 0, "final": 0}
    try:
        raw_records = scraper.scrape(max_pages=max_pages)
    except Exception:
        logger.exception("%s: scraper crashed, continuing with the other source", name)
        return [], stats
    stats["raw"] = len(raw_records)

    reasons = Counter()
    valid = []
    scraped_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for raw in raw_records:
        try:
            rec = cleaner(raw, scraped_at)
        except Exception as exc:
            logger.warning("%s: cleaning failed (%s): %r", name, exc, raw)
            reasons["cleaning_error"] += 1
            continue
        stats["cleaned"] += 1
        problems = validate_record(rec)
        if problems:
            logger.warning("%s: rejected %r because %s", name, rec.get("name_or_title"), problems)
            for p in problems:
                reasons[p] += 1
            stats["rejected"] += 1
            continue
        valid.append(rec)

    # records that failed cleaning also count as rejected
    stats["rejected"] += reasons["cleaning_error"]
    stats["rejected_by_reason"] = dict(reasons)

    unique, dupes = find_duplicates(valid)
    for d in dupes:
        logger.info("%s: duplicate removed: %r", name, d["name_or_title"])
    stats["duplicates"] = len(dupes)
    stats["final"] = len(unique)
    return unique, stats


def write_csv(records, path):
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser(description="Scrape books and quotes into one dataset.")
    parser.add_argument("--max-pages", type=int, default=None,
                        help="limit pages per source (handy for quick tests)")
    parser.add_argument("--no-details", action="store_true",
                        help="skip book detail pages (faster, but category/description stay empty)")
    args = parser.parse_args()

    setup_logging()
    start = time.time()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    session = create_session()

    sources = [
        ("Books to Scrape", BooksScraper(session, fetch_details=not args.no_details), clean_book),
        ("Quotes to Scrape", QuotesScraper(session), clean_quote),
    ]
    final, per_source = [], {}
    for name, scraper, cleaner in sources:
        records, stats = process_source(name, scraper, cleaner, args.max_pages)
        final.extend(records)
        per_source[name] = stats

    write_csv(final, OUTPUT_DIR / "final_dataset.csv")

    summary = {
        "per_source": per_source,
        "totals": {
            "raw": sum(s["raw"] for s in per_source.values()),
            "cleaned": sum(s["cleaned"] for s in per_source.values()),
            "rejected": sum(s["rejected"] for s in per_source.values()),
            "duplicates": sum(s["duplicates"] for s in per_source.values()),
            "final": len(final),
        },
        "started_at": started_at,
        "ended_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duration_seconds": round(time.time() - start, 1),
    }
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_DIR / "summary_report.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
    logger.info("Done: %d rows written. %s", len(final), summary["totals"])


if __name__ == "__main__":
    main()
