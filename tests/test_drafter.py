"""
Unit tests for comment_drafter and similarity_checker.
"""
from unittest.mock import MagicMock

from drafting.comment_drafter import draft_comment
from drafting.similarity_checker import is_too_similar


def _make_drafter_mock(text: str):
    mock = MagicMock()
    mock.messages.create.return_value.content = [MagicMock(text=text)]
    return mock


def test_draft_clean_comment():
    thread = {
        "reddit_post_id": "abc123",
        "subreddit": "carbuying",
        "title": "Is month-to-month car leasing worth it?",
        "body": "I'm thinking about it but not sure.",
    }
    claude = _make_drafter_mock("Honestly, it depends on your situation. I tried Flexcar and loved the flexibility.")
    result = draft_comment(thread, claude, past_comments=[])
    assert result["safe_to_queue"] is True
    assert "car subscription" not in result["draft_text"]


def test_draft_strips_links():
    thread = {
        "reddit_post_id": "def456",
        "subreddit": "cars",
        "title": "Car options?",
        "body": "",
    }
    claude = _make_drafter_mock("Check out https://flexcar.com for more info!")
    result = draft_comment(thread, claude, past_comments=[])
    assert "https://" not in result["draft_text"]
    assert result["safety_flags"]["links_stripped"] is True


def test_draft_banned_term_blocks():
    thread = {
        "reddit_post_id": "ghi789",
        "subreddit": "personalfinance",
        "title": "Looking for rideshare alternative",
        "body": "",
    }
    claude = _make_drafter_mock("Try using rideshare or Flexcar!")
    result = draft_comment(thread, claude, past_comments=[])
    assert result["safe_to_queue"] is False
    assert "rideshare" in result["safety_flags"]["banned_terms"]


def test_similarity_too_high():
    past = ["I personally use Flexcar and love the flexibility of no long contract."]
    draft = "I personally use Flexcar and love the flexibility of no long contract."
    flagged, score = is_too_similar(draft, past)
    assert flagged is True
    assert score > 0.9


def test_similarity_low():
    past = ["Totally different topic about cooking pasta."]
    draft = "Flexcar offers month to month car leasing in Boston and Atlanta."
    flagged, score = is_too_similar(draft, past)
    assert flagged is False
