"""
Enforces the daily posting cap (max 3 posts/day) with randomized timing.
Reads today's posted count from Supabase; falls back to an in-memory counter
when the DB is unavailable.
"""
from __future__ import annotations

import random
from datetime import date, datetime, timezone

MAX_POSTS_PER_DAY = 3
MIN_MINUTES_BETWEEN_POSTS = 90
TIMING_JITTER_MINUTES = 30

_in_memory_count: int = 0
_last_post_time: datetime | None = None


def can_post_today(db_posts_today: int | None = None) -> bool:
    """Return True if we are under the daily cap."""
    count = db_posts_today if db_posts_today is not None else _in_memory_count
    return count < MAX_POSTS_PER_DAY


def minutes_until_next_allowed() -> int:
    """
    Return how many minutes to wait before the next post is allowed.
    0 means posting is allowed immediately.
    Adds ±30 min jitter to avoid predictable timing patterns.
    """
    if _last_post_time is None:
        return 0

    elapsed = (datetime.now(tz=timezone.utc) - _last_post_time).total_seconds() / 60
    jitter = random.randint(-TIMING_JITTER_MINUTES, TIMING_JITTER_MINUTES)
    required = MIN_MINUTES_BETWEEN_POSTS + jitter

    remaining = required - elapsed
    return max(0, int(remaining))


def record_post() -> None:
    """Increment in-memory counter after a post is approved and sent."""
    global _in_memory_count, _last_post_time
    _in_memory_count += 1
    _last_post_time = datetime.now(tz=timezone.utc)


def get_posts_today_from_db(supabase_client) -> int:
    """Query Supabase for how many comments were posted today."""
    today = date.today().isoformat()
    try:
        result = (
            supabase_client
            .table("post_history")
            .select("id", count="exact")
            .gte("created_at", today)
            .execute()
        )
        return result.count or 0
    except Exception as e:
        print(f"[frequency] could not query DB: {e}")
        return 0
