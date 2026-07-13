"""
Read/write helpers for each Supabase table.
All functions accept a supabase client to keep them testable without globals.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any


# ── reddit_threads ──────────────────────────────────────────────────────────

def get_existing_post_ids(client) -> set[str]:
    """Return the set of reddit_post_id values already in the table."""
    try:
        result = client.table("reddit_threads").select("reddit_post_id").execute()
        return {row["reddit_post_id"] for row in (result.data or [])}
    except Exception as e:
        print(f"[db] get_existing_post_ids failed: {e}")
        return set()


def upsert_thread(client, thread: dict) -> dict | None:
    """Insert a thread or update if the post_id already exists."""
    payload = {
        "reddit_post_id": thread["reddit_post_id"],
        "subreddit": thread["subreddit"],
        "title": thread["title"],
        "body": thread.get("body", ""),
        "author": thread.get("author"),
        "url": thread.get("url"),
        "posted_at": thread.get("posted_at"),
        "relevance_score": thread.get("relevance_score"),
        "opportunity_rank": thread.get("opportunity_rank"),
        "status": thread.get("status", "new"),
    }
    try:
        result = (
            client.table("reddit_threads")
            .upsert(payload, on_conflict="reddit_post_id")
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"[db] upsert_thread failed: {e}")
        return None


def update_thread_status(client, reddit_post_id: str, status: str) -> None:
    try:
        client.table("reddit_threads").update({"status": status}).eq(
            "reddit_post_id", reddit_post_id
        ).execute()
    except Exception as e:
        print(f"[db] update_thread_status failed: {e}")


# ── comment_drafts ──────────────────────────────────────────────────────────

def save_draft(client, draft: dict, thread_db_id: int) -> dict | None:
    payload = {
        "thread_id": thread_db_id,
        "draft_text": draft["draft_text"],
        "similarity_score": draft.get("similarity_score"),
        "safety_flags": draft.get("safety_flags"),
    }
    try:
        result = client.table("comment_drafts").insert(payload).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"[db] save_draft failed: {e}")
        return None


def get_pending_drafts(client) -> list[dict]:
    try:
        result = (
            client.table("comment_drafts")
            .select("*, reddit_threads(*)")
            .is_("approved_at", "null")
            .is_("posted_at", "null")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"[db] get_pending_drafts failed: {e}")
        return []


def approve_draft(client, draft_id: int, approved_by: str, edited_text: str | None = None) -> None:
    update = {
        "approved_by": approved_by,
        "approved_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    if edited_text:
        update["edited_text"] = edited_text
    try:
        client.table("comment_drafts").update(update).eq("id", draft_id).execute()
    except Exception as e:
        print(f"[db] approve_draft failed: {e}")


def reject_draft(client, draft_id: int) -> None:
    try:
        client.table("comment_drafts").delete().eq("id", draft_id).execute()
    except Exception as e:
        print(f"[db] reject_draft failed: {e}")


def mark_draft_posted(client, draft_id: int, reddit_comment_id: str) -> None:
    try:
        client.table("comment_drafts").update(
            {
                "posted_at": datetime.now(tz=timezone.utc).isoformat(),
                "reddit_comment_id": reddit_comment_id,
            }
        ).eq("id", draft_id).execute()
    except Exception as e:
        print(f"[db] mark_draft_posted failed: {e}")


# ── post_history ────────────────────────────────────────────────────────────

def get_recent_comment_texts(client, limit: int = 100) -> list[str]:
    """Used by the similarity checker to compare new drafts against past posts."""
    try:
        result = (
            client.table("post_history")
            .select("comment_text")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [row["comment_text"] for row in (result.data or [])]
    except Exception as e:
        print(f"[db] get_recent_comment_texts failed: {e}")
        return []


def save_to_post_history(client, subreddit: str, comment_text: str, thread_url: str) -> None:
    try:
        client.table("post_history").insert(
            {
                "subreddit": subreddit,
                "comment_text": comment_text,
                "thread_url": thread_url,
            }
        ).execute()
    except Exception as e:
        print(f"[db] save_to_post_history failed: {e}")


# ── monitored_subreddits ────────────────────────────────────────────────────

def get_active_subreddits(client) -> list[str]:
    try:
        result = (
            client.table("monitored_subreddits")
            .select("name")
            .eq("active", True)
            .neq("safety_rating", "red")
            .execute()
        )
        return [row["name"] for row in (result.data or [])]
    except Exception as e:
        print(f"[db] get_active_subreddits failed: {e}")
        return []
