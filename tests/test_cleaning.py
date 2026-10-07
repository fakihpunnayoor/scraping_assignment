from processing.cleaning import (clean_price, clean_rating, clean_tags, clean_text,
                                 normalize_url, strip_quotes)


def test_clean_text():
    assert clean_text("  Hello \n World ") == "Hello World"
    assert clean_text("a\xa0b") == "a b"
    assert clean_text("   ") is None
    assert clean_text(None) is None


def test_strip_quotes():
    assert strip_quotes("\u201cThe world is big.\u201d") == "The world is big."


def test_clean_price():
    assert clean_price("\u00a351.77") == 51.77
    assert clean_price("\u00c2\u00a351.77") == 51.77   # mojibake still works
    assert clean_price("free") is None
    assert clean_price(None) is None


def test_clean_rating():
    assert clean_rating("star-rating Three") == 3
    assert clean_rating("star-rating") is None


def test_clean_tags():
    assert clean_tags(["Love", " books ", "love"]) == "books;love"
    assert clean_tags([]) is None


def test_normalize_url():
    assert normalize_url(" https://a.com/x ") == "https://a.com/x"
    assert normalize_url("/relative") is None
    assert normalize_url("ftp://a.com") is None
