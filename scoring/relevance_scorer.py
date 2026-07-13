"""
Sends a thread to Claude and returns a relevance score 0-100.
"""
from __future__ import annotations

import json

from drafting.prompt_templates import RELEVANCE_SCORER_SYSTEM_PROMPT

RELEVANCE_THRESHOLD = 65


def score_thread(thread: dict, claude_client) -> dict:
    """
    Returns the thread dict enriched with:
        relevance_score: int (0-100)
        score_reason: str
        opportunity_type: str
    """
    content = f"Title: {thread['title']}\n\nBody: {thread['body']}"

    message = claude_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=128,
        system=RELEVANCE_SCORER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    raw = message.content[0].text.strip()
    try:
        parsed = json.loads(raw)
        score = int(parsed.get("score", 0))
        reason = parsed.get("reason", "")
        opportunity_type = parsed.get("opportunity_type", "general")
    except (json.JSONDecodeError, ValueError):
        score = 0
        reason = f"Parse error: {raw[:200]}"
        opportunity_type = "general"

    thread["relevance_score"] = score
    thread["score_reason"] = reason
    thread["opportunity_type"] = opportunity_type

    print(
        f"[scorer] r/{thread['subreddit']} | score={score} | {opportunity_type} | {reason[:80]}"
    )
    return thread


def passes_threshold(thread: dict, threshold: int = RELEVANCE_THRESHOLD) -> bool:
    return thread.get("relevance_score", 0) >= threshold
