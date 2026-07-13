"""
Pulls subreddit rules and asks Claude to rate safety for flexcar_sam engagement.
Returns Green / Yellow / Red with a reason.
"""
from __future__ import annotations

import json

from monitor.reddit_client import get_reddit_client, safe_reddit_call
from drafting.prompt_templates import RULES_CHECKER_SYSTEM_PROMPT

_rules_cache: dict[str, dict] = {}


def get_subreddit_rules_text(subreddit_name: str) -> str:
    """Fetch rules text for a subreddit via PRAW."""
    reddit = get_reddit_client()
    try:
        sub = safe_reddit_call(reddit.subreddit, subreddit_name)
        rules = safe_reddit_call(list, sub.rules())
        if not rules:
            return "No explicit rules found."
        parts = []
        for rule in rules:
            parts.append(f"Rule: {rule.short_name}\n{rule.description or ''}")
        return "\n\n".join(parts)
    except Exception as e:
        return f"Could not retrieve rules: {e}"


def check_subreddit_safety(subreddit_name: str, claude_client=None) -> dict:
    """
    Returns {"rating": "green|yellow|red", "reason": "...", "key_rules": [...]}

    Uses a cache so we don't re-check the same sub in a single run.
    Pass a live anthropic client to actually call Claude; without it the
    function returns a placeholder (useful for unit tests / offline runs).
    """
    if subreddit_name in _rules_cache:
        return _rules_cache[subreddit_name]

    rules_text = get_subreddit_rules_text(subreddit_name)

    if claude_client is None:
        result = {
            "rating": "yellow",
            "reason": "Rules check skipped — no Claude client provided.",
            "key_rules": [],
        }
        _rules_cache[subreddit_name] = result
        return result

    message = claude_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        system=RULES_CHECKER_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Subreddit: r/{subreddit_name}\n\nRules:\n{rules_text}",
            }
        ],
    )

    raw = message.content[0].text.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "rating": "yellow",
            "reason": f"Could not parse Claude response: {raw[:200]}",
            "key_rules": [],
        }

    _rules_cache[subreddit_name] = result
    print(f"[rules] r/{subreddit_name} → {result['rating'].upper()}: {result['reason']}")
    return result
