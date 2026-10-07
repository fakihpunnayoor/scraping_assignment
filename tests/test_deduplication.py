from processing.deduplication import find_duplicates


def test_books_ignore_case_and_spaces():
    base = {"source": "Books to Scrape", "author": None}
    records = [{**base, "name_or_title": t}
               for t in ("Example Book Title", "  Example Book Title ", "EXAMPLE BOOK TITLE")]
    unique, dupes = find_duplicates(records)
    assert len(unique) == 1 and len(dupes) == 2


def test_quotes_same_text_different_author_are_not_duplicates():
    base = {"source": "Quotes to Scrape", "name_or_title": "Be yourself."}
    unique, dupes = find_duplicates([{**base, "author": "A"}, {**base, "author": "B"}])
    assert len(unique) == 2 and not dupes


def test_same_title_in_different_sources_is_kept():
    a = {"source": "Books to Scrape", "name_or_title": "Hello", "author": None}
    b = {"source": "Quotes to Scrape", "name_or_title": "Hello", "author": ""}
    unique, _ = find_duplicates([a, b])
    assert len(unique) == 2
