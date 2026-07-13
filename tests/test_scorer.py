"""
Unit tests for relevance_scorer and opportunity_ranker.
Uses a mock Claude client — no real API calls.
"""
from unittest.mock import MagicMock
import json

from scoring.relevance_scorer import score_thread, passes_threshold
from scoring.opportunity_ranker import rank_and_filter


def _make_claude_mock(score: int, reason: str = "test", opportunity_type: str = "question"):
    mock = MagicMock()
    mock.messages.create.return_value.content = [
        MagicMock(text=json.dumps({"score": score, "reason": reason, "opportunity_type": opportunity_type}))
    ]
    return mock


def test_score_thread_above_threshold():
    thread = {"subreddit": "carbuying", "title": "Best flexible car lease?", "body": ""}
    claude = _make_claude_mock(score=82)
    result = score_thread(thread, claude)
    assert result["relevance_score"] == 82
    assert passes_threshold(result)


def test_score_thread_below_threshold():
    thread = {"subreddit": "cars", "title": "Nice car paint job", "body": ""}
    claude = _make_claude_mock(score=30)
    result = score_thread(thread, claude)
    assert not passes_threshold(result)


def test_rank_and_filter_sorts_descending():
    threads = [
        {"relevance_score": 70},
        {"relevance_score": 90},
        {"relevance_score": 65},
        {"relevance_score": 50},  # below threshold
    ]
    ranked = rank_and_filter(threads)
    assert len(ranked) == 3
    assert ranked[0]["relevance_score"] == 90
    assert ranked[0]["opportunity_rank"] == 1
    assert ranked[2]["opportunity_rank"] == 3


def test_rank_and_filter_empty():
    assert rank_and_filter([]) == []
