"""Books to Scrape: selectors and parsing live here and nowhere else."""
import logging
from urllib.parse import urljoin

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BooksScraper(BaseScraper):
    SOURCE = "Books to Scrape"
    START_URL = "https://books.toscrape.com/"

    def __init__(self, session=None, fetch_details=True):
        super().__init__(session)
        self.fetch_details = fetch_details

    def parse_page(self, soup, page_url):
        records = []
        for article in soup.select("article.product_pod"):
            try:
                records.append(self.parse_book(article, page_url))
            except Exception as exc:  # one bad record must not stop the page
                logger.warning("Skipping a book on %s: %s", page_url, exc)
        return records

    def parse_book(self, article, page_url):
        link = article.select_one("h3 > a")
        price = article.select_one("p.price_color")
        rating = article.select_one("p.star-rating")
        raw = {
            "title": link.get("title") if link else None,  # visible text is cut off with "..."
            "url": urljoin(page_url, link["href"]) if link and link.get("href") else None,
            "price_raw": price.get_text() if price else None,
            "rating_raw": " ".join(rating.get("class", [])) if rating else None,
            "category": None,
            "description": None,
        }
        if self.fetch_details and raw["url"]:
            self.add_details(raw)
        return raw

    def add_details(self, raw):
        """Category and description only exist on the detail page."""
        soup = self.get_soup(raw["url"])
        if soup is None:
            logger.warning("No detail page for %r, category/description left empty", raw["title"])
            return
        crumbs = soup.select("ul.breadcrumb li a")
        if len(crumbs) >= 3:
            raw["category"] = crumbs[2].get_text()
        desc = soup.select_one("#product_description ~ p")
        if desc:
            raw["description"] = desc.get_text()
