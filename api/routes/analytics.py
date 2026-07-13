"""
GET /analytics/weekly       — weekly snapshot summary
GET /analytics/subreddits   — per-subreddit performance breakdown
GET /analytics/history      — comment history with status and engagement
"""
from __future__ import annotations

from fastapi import APIRouter
from database.supabase_client import get_supabase_client

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/weekly")
def get_weekly():
    """Returns the most recent analytics snapshot."""
    client = get_supabase_client()
    try:
        result = (
            client.table("analytics_snapshots")
            .select("*")
            .order("week_start", desc=True)
            .limit(12)
            .execute()
        )
        return {"snapshots": result.data or []}
    except Exception as e:
        return {"error": str(e), "snapshots": []}


@router.get("/subreddits")
def get_subreddit_stats():
    """Per-subreddit breakdown: how many posts came from each sub."""
    client = get_supabase_client()
    try:
        result = (
            client.table("post_history")
            .select("subreddit")
            .execute()
        )
        rows = result.data or []
        counts: dict[str, int] = {}
        for row in rows:
            sub = row["subreddit"]
            counts[sub] = counts.get(sub, 0) + 1
        breakdown = sorted(
            [{"subreddit": k, "posts": v} for k, v in counts.items()],
            key=lambda x: x["posts"],
            reverse=True,
        )
        return {"subreddits": breakdown}
    except Exception as e:
        return {"error": str(e), "subreddits": []}


@router.get("/history")
def get_comment_history(limit: int = 50):
    """Comment history with thread URL and karma context."""
    client = get_supabase_client()
    try:
        result = (
            client.table("post_history")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {"history": result.data or []}
    except Exception as e:
        return {"error": str(e), "history": []}
