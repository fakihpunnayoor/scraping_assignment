"""Offline tests: parsers and the full pipeline run against a fake website (no internet)."""
import csv
import json

import main
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

BOOKS_P1 = """<ul><li class="next"><a href="page-2.html">next</a></li></ul>
<article class="product_pod"><h3><a href="a-book_1/index.html" title="A Light in the Attic">A Light in th...</a></h3>
<p class="star-rating Three"></p><p class="price_color">\u00a351.77</p></article>
<article class="product_pod"><p>broken record with no link, price or rating</p></article>"""
BOOKS_P2 = """<article class="product_pod"><h3><a href="b-book_2/index.html" title="Tipping the Velvet">T...</a></h3>
<p class="star-rating One"></p><p class="price_color">\u00a353.74</p></article>"""
BOOK_DETAIL = """<ul class="breadcrumb"><li><a>Home</a></li><li><a>Books</a></li><li><a>Poetry</a></li></ul>
<div id="product_description"></div><p>  A   nice\xa0book. </p>"""
QUOTES_P1 = """<div class="quote"><span class="text">\u201cBe yourself.\u201d</span><span><small class="author">Oscar Wilde</small></span>
<div class="tags"><a class="tag">Life</a><a class="tag">truth</a></div></div>
<div class="quote"><span class="text">\u201cBe yourself.\u201d</span><span><small class="author">Oscar Wilde</small></span></div>"""


class FakeResponse:
    def __init__(self, text, status=200):
        self.text, self.status_code, self.encoding = text, status, None

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(str(self.status_code))


class FakeSession:
    PAGES = {
        "https://books.toscrape.com/": BOOKS_P1,
        "https://books.toscrape.com/page-2.html": BOOKS_P2,
        "https://books.toscrape.com/a-book_1/index.html": BOOK_DETAIL,
        "https://books.toscrape.com/b-book_2/index.html": BOOK_DETAIL,
        "https://quotes.toscrape.com/": QUOTES_P1,
    }

    def get(self, url, timeout=None):
        if url not in self.PAGES:
            return FakeResponse("", 500)
        return FakeResponse(self.PAGES[url])


def fast(scraper):
    scraper.DELAY = 0
    return scraper


def test_books_pagination_details_and_bad_record():
    raw = fast(BooksScraper(FakeSession())).scrape()
    titles = [r["title"] for r in raw if r["title"]]
    assert titles == ["A Light in the Attic", "Tipping the Velvet"]   # followed "next"
    assert raw[0]["category"] == "Poetry"


def test_failed_page_does_not_crash():
    class Broken(FakeSession):
        PAGES = {}
    assert fast(BooksScraper(Broken())).scrape() == []


def test_quotes_parser():
    raw = fast(QuotesScraper(FakeSession())).scrape()
    assert raw[0]["author"] == "Oscar Wilde" and raw[0]["tags"] == ["Life", "truth"]


def test_full_pipeline_counts_reconcile(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main, "create_session", lambda: FakeSession())
    monkeypatch.setattr("sys.argv", ["main.py"])
    monkeypatch.setattr(main, "LOG_FILE", tmp_path / "scraper.log")
    monkeypatch.setattr("scrapers.base_scraper.BaseScraper.DELAY", 0)
    main.main()

    summary = json.loads((tmp_path / "summary_report.json").read_text())
    rows = list(csv.DictReader(open(tmp_path / "final_dataset.csv", encoding="utf-8")))
    t = summary["totals"]
    assert t["final"] == len(rows) == 3          # 2 books + 1 unique quote
    assert t["duplicates"] == 1                  # the repeated quote
    assert t["raw"] - t["rejected"] - t["duplicates"] == t["final"]
    assert {r["source"] for r in rows} == {"Books to Scrape", "Quotes to Scrape"}
    assert rows[0]["price"] == "51.77" and rows[0]["rating"] == "3"
