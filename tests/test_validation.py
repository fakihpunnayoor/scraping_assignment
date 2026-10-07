from processing.validation import validate_record


def good():
    return {"source": "Books to Scrape", "name_or_title": "X", "source_url": "https://a.com",
            "price": 10.0, "rating": 3}


def test_valid_record():
    assert validate_record(good()) == []


def test_each_problem_is_reported():
    rec = {"source": "Nope", "name_or_title": None, "source_url": "bad", "price": -1, "rating": 9}
    assert set(validate_record(rec)) == {"unknown_source", "missing_name", "invalid_url",
                                         "invalid_price", "invalid_rating"}


def test_missing_price_and_rating_are_fine():
    rec = good() | {"price": None, "rating": None}
    assert validate_record(rec) == []
