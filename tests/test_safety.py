"""
Unit tests for the safety module.
"""
from safety.banned_terms import contains_banned_term
from safety.link_stripper import strip_links, has_links
from safety.frequency_limiter import can_post_today


def test_banned_term_detected():
    found, matched = contains_banned_term("This is a car subscription service.")
    assert found is True
    assert "car subscription" in matched


def test_no_banned_term():
    found, matched = contains_banned_term("I love driving my car every day.")
    assert found is False
    assert matched == []


def test_link_stripped():
    result = strip_links("Check out https://flexcar.com for details!")
    assert "https://" not in result
    assert "flexcar.com" not in result


def test_no_link():
    text = "Just a normal sentence."
    assert strip_links(text) == text
    assert has_links(text) is False


def test_has_link():
    assert has_links("Visit http://example.com today") is True


def test_can_post_under_cap():
    assert can_post_today(db_posts_today=2) is True


def test_cannot_post_at_cap():
    assert can_post_today(db_posts_today=3) is False
