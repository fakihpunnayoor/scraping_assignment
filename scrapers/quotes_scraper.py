"""Quotes to Scrape: selectors and parsing live here and nowhere else."""
import logging

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class QuotesScraper(BaseScraper):
    SOURCE = "Quotes to Scrape"
    START_URL = "https://quotes.toscrape.com/"

    def parse_page(self, soup, page_url):
        records = []
        for div in soup.select("div.quote"):
            try:
                text = div.select_one("span.text")
                author = div.select_one("small.author")
                records.append({
                    "text": text.get_text() if text else None,
                    "author": author.get_text() if author else None,
                    "tags": [t.get_text() for t in div.select("a.tag")],
                    "page_url": page_url,
                })
            except Exception as exc:
                logger.warning("Skipping a quote on %s: %s", page_url, exc)
        return records
