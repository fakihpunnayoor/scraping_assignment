"""Shared networking code: session, retries, timeout, polite delay, pagination loop."""
import logging
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger(__name__)


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "ScrapingAssignment/1.0 (learning project)"})
    retries = Retry(total=3, backoff_factor=1.0,
                    status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class BaseScraper:
    SOURCE = ""
    START_URL = ""
    DELAY = 0.5
    TIMEOUT = 10

    def __init__(self, session=None):
        self.session = session or create_session()

    def get_soup(self, url):
        """Download one page. Returns a BeautifulSoup object, or None if it failed."""
        try:
            response = self.session.get(url, timeout=self.TIMEOUT)
            response.raise_for_status()
            response.encoding = "utf-8"  # keeps the pound sign correct
        except requests.RequestException as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
            return None
        finally:
            time.sleep(self.DELAY)
        return BeautifulSoup(response.text, "lxml")

    def parse_page(self, soup, page_url):
        raise NotImplementedError

    def scrape(self, max_pages=None):
        """Follow the 'next' link until there is none. Returns a list of raw dicts."""
        url, page, records = self.START_URL, 1, []
        while url and (max_pages is None or page <= max_pages):
            logger.info("[%s] page %d: %s", self.SOURCE, page, url)
            soup = self.get_soup(url)
            if soup is None:
                logger.error("[%s] stopping at page %d because it could not be fetched",
                             self.SOURCE, page)
                break
            records.extend(self.parse_page(soup, url))
            next_link = soup.select_one("li.next > a")
            url = urljoin(url, next_link["href"]) if next_link and next_link.get("href") else None
            page += 1
        logger.info("[%s] scraped %d raw records", self.SOURCE, len(records))
        return records
