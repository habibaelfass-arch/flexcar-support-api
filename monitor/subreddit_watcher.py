"""
Fetches recent posts from target subreddits.
Returns a list of normalized thread dicts ready for the pipeline.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from monitor.reddit_client import get_reddit_client, safe_reddit_call

TARGET_SUBREDDITS: list[str] = [
    # Green — high opportunity
    "askcarsales",
    "cars",
    "carbuying",
    "Atlanta",
    "boston",
    "Charlotte",
    "nashville",
    "AskNYC",
    "SanFrancisco",
    "moving",
    "frugal",
    # Yellow — proceed carefully
    "personalfinance",
    "leasehackr",
    "financialindependence",
    "povertyfinance",
]

HIGH_RELEVANCE_KEYWORDS: list[str] = [
    "car lease", "month to month", "monthly car",
    "flexible lease", "car subscription", "hate my lease",
    "car payment too high", "stuck in lease",
    "need a car short term", "temporary car",
    "moving to atlanta", "moving to boston",
    "moving to charlotte", "moving to nashville",
    "moving to new york", "moving to san francisco",
    "car insurance included", "all inclusive car",
]

BRAND_MENTIONS: list[str] = ["flexcar", "flex car"]

COMPETITOR_MENTIONS: list[str] = [
    "fair.com", "autonomy", "sixt", "hertz my car", "canvas",
]


def _normalize_post(post: Any) -> dict:
    """Convert a PRAW submission into a plain dict."""
    return {
        "reddit_post_id": post.id,
        "subreddit": post.subreddit.display_name,
        "title": post.title,
        "body": post.selftext or "",
        "author": str(post.author) if post.author else "[deleted]",
        "url": f"https://reddit.com{post.permalink}",
        "posted_at": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat(),
        "keyword_matches": _find_keywords(post.title + " " + (post.selftext or "")),
        "competitor_mentions": _find_competitors(post.title + " " + (post.selftext or "")),
        "brand_mentions": _find_brand(post.title + " " + (post.selftext or "")),
    }


def _find_keywords(text: str) -> list[str]:
    text_lower = text.lower()
    return [kw for kw in HIGH_RELEVANCE_KEYWORDS if kw in text_lower]


def _find_competitors(text: str) -> list[str]:
    text_lower = text.lower()
    return [c for c in COMPETITOR_MENTIONS if c in text_lower]


def _find_brand(text: str) -> list[str]:
    text_lower = text.lower()
    return [b for b in BRAND_MENTIONS if b in text_lower]


def fetch_recent_posts(
    subreddits: list[str] | None = None,
    limit_per_sub: int = 50,
) -> list[dict]:
    """
    Pull the most recent `limit_per_sub` posts from each subreddit.
    Returns a flat list of normalized thread dicts.
    """
    reddit = get_reddit_client()
    subs = subreddits or TARGET_SUBREDDITS
    threads: list[dict] = []

    for sub_name in subs:
        try:
            subreddit = safe_reddit_call(reddit.subreddit, sub_name)
            posts = safe_reddit_call(list, subreddit.new(limit=limit_per_sub))
            if not posts:
                continue
            for post in posts:
                if post.is_self or post.selftext:
                    threads.append(_normalize_post(post))
        except Exception as e:
            print(f"[watcher] skipping r/{sub_name}: {e}")
            continue

    print(f"[watcher] fetched {len(threads)} posts from {len(subs)} subreddits")
    return threads
