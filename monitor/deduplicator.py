"""
Prevents processing the same Reddit thread twice.
Checks against Supabase. Falls back to an in-memory set when DB is unavailable.
"""
from __future__ import annotations

_seen_ids: set[str] = set()


def filter_new_threads(threads: list[dict], db_seen_ids: set[str] | None = None) -> list[dict]:
    """
    Return only threads whose reddit_post_id has not been processed before.

    `db_seen_ids` should be the set of post IDs already in the `reddit_threads` table.
    If not provided, only the in-memory set is used (safe for a single run).
    """
    known = (db_seen_ids or set()) | _seen_ids
    new_threads = [t for t in threads if t["reddit_post_id"] not in known]

    for t in new_threads:
        _seen_ids.add(t["reddit_post_id"])

    print(f"[dedup] {len(threads)} fetched → {len(new_threads)} new after dedup")
    return new_threads


def mark_seen(post_id: str) -> None:
    """Manually mark a post ID as seen in the in-memory cache."""
    _seen_ids.add(post_id)
