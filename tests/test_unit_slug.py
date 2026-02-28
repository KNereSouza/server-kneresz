from app.utils.slug import generate_slug


def test_generate_slug_basic():
    assert generate_slug("Hello World") == "hello-world"


def test_generate_slug_special_characters():
    assert generate_slug("C++ is Great! (or not?)") == "c-is-great-or-not"


def test_generate_slug_unicode():
    result = generate_slug("Cafe Resume")
    assert result == "cafe-resume"


def test_generate_slug_max_length():
    long_title = "a" * 300
    result = generate_slug(long_title)
    assert len(result) <= 200


def test_generate_slug_empty_string():
    assert generate_slug("") == ""
