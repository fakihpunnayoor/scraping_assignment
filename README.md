# Multi-Source Web Scraping & Data Consolidation

A small ETL pipeline that scrapes **Books to Scrape** and **Quotes to Scrape**, cleans and validates the
data, removes duplicates, and writes one CSV plus a JSON summary.

```
Scrape -> Clean -> Validate -> Deduplicate -> Consolidate -> Save
```

## Python version
3.10, 3.11 or 3.12.

## Setup
```
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
Dependencies: `requests`, `beautifulsoup4`, `lxml`, `pytest` (tests only).

## How to run
```
python main.py                    # full run (see note on run time below)
python main.py --no-details       # skip book detail pages: much faster, category/description empty
python main.py --max-pages 2      # quick test: 2 pages per source
python -m pytest                  # unit tests, no internet needed
```
Outputs: `output/final_dataset.csv`, `output/summary_report.json`, `logs/scraper.log`.

**Run time:** the books site lists no category or description on its listing pages, so by default
the scraper opens every book's detail page (~1,000 extra requests). With a 0.5 s pause per request a full
run takes roughly 10-15 minutes. Use `--no-details` for a ~1 minute run.

## What I found on the sites (Step 1)
| Item | Books to Scrape | Quotes to Scrape |
|---|---|---|
| One record | `article.product_pod` | `div.quote` |
| Main text | `h3 > a`, full title is in the `title` attribute (visible text is cut with `...`) | `span.text` (in curly quotes) |
| Price | `p.price_color` | none |
| Rating | class on `p.star-rating` (a word, e.g. `Three`) | none |
| Author / tags | none | `small.author`, `a.tag` (zero or more) |
| Link | `h3 > a[href]`, relative path | none used (see data model) |
| Category / description | only on the detail page (breadcrumb, `#product_description + p`) | none |
| Next page | `li.next > a` | `li.next > a` |

## How pagination works
`BaseScraper.scrape()` downloads a page, parses it, then looks for `li.next > a`. If it exists, the relative
link is turned into a full URL with `urljoin` and the loop repeats. If not, it stops. No page numbers are
hard-coded, so it keeps working if the site gains or loses pages.

## Data model
Both sources share these columns. Fields that don't apply are left empty (nothing is invented).

| Column | Books | Quotes |
|---|---|---|
| source | Books to Scrape | Quotes to Scrape |
| source_url | book detail page URL | URL of the page the quote appeared on |
| name_or_title | title | quote text (curly quotes removed) |
| category | from detail page | fixed label `Quotes` |
| price | float (51.77) | empty |
| rating | int 1-5 | empty |
| author | empty | author name |
| tags | empty | `tag1;tag2` (lowercase, sorted) |
| description | from detail page | empty |
| scraped_at | UTC timestamp | UTC timestamp |

I chose a single flat table because it is what the CSV needs and it is easy to filter by `source`.

## Cleaning approach (`processing/cleaning.py`)
Small pure functions, tested without internet: collapse whitespace and `\xa0`, strip curly quotes, turn
`£51.77` into `51.77`, turn `Three` into `3`, lowercase/sort/join tags, and accept only full `http(s)` URLs.
Empty strings become `None`. Responses are decoded as UTF-8 so `£` stays correct.

## Validation approach (`processing/validation.py`)
Each record returns a list of problems: `unknown_source`, `missing_name`, `invalid_url`, `invalid_price`
(not a number or negative), `invalid_rating` (not 1-5). Bad records are logged as warnings, counted by reason
in the summary, and left out of the CSV.

## Deduplication approach (`processing/deduplication.py`)
A fingerprint is built from the identifying fields, lowercased, punctuation removed, spaces collapsed, then
hashed with SHA-256.
- Books: source + title
- Quotes: source + author + first 50 characters of the quote

The first copy is kept; later copies are **removed** (not flagged), because the final file should be tidy and
every removed duplicate is still counted in the summary and logged. The real sites have no duplicates, so
this is proven with unit tests that use deliberately duplicated data.

## Error handling approach
- Requests use a session with 3 retries and exponential backoff on 429/500/502/503/504, plus a 10 s timeout.
- A page that still fails is logged as an ERROR and that source stops with what it already has; the other source still runs.
- Each record is parsed inside `try/except`; missing elements are checked for `None` first.
- A book whose detail page fails is kept, with empty category/description (logged as a warning).
- Each source is wrapped in its own `try/except` in `main.py`.

## Output description
- `final_dataset.csv`: one row per unique, valid record, fixed column order.
- `summary_report.json`: per-source and total counts of raw, cleaned, rejected (with reasons), duplicates, final, plus start/end time and duration. Numbers reconcile: raw - rejected - duplicates = final.
- `logs/scraper.log`: every page, warning and error.

## Assumptions
- The two practice sites keep their current HTML structure.
- A quote's `source_url` is the page it appeared on (the quotes are not individually linkable).
- Two quotes by the same author with the same first 50 characters count as the same quote.

## Known limitations
- Sequential scraping (polite but slow); no checkpoint/resume.
- If a listing page fails, scraping of that source stops there rather than skipping ahead.
- Author "about" pages on the quotes site are not scraped.
- The fake-site tests cover the logic, but selectors still depend on the live HTML.

## AI usage summary
See `AI_USAGE.md`.
