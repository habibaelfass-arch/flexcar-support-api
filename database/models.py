"""
Pydantic models matching the Supabase table schemas.
Used for type safety when reading/writing from the DB.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel


class MonitoredSubreddit(BaseModel):
    id: Optional[int] = None
    name: str
    rules_text: Optional[str] = None
    safety_rating: Literal["green", "yellow", "red"] = "yellow"
    active: bool = True
    last_rules_check: Optional[datetime] = None
    created_at: Optional[datetime] = None


class RedditThread(BaseModel):
    id: Optional[int] = None
    reddit_post_id: str
    subreddit: str
    title: str
    body: Optional[str] = None
    author: Optional[str] = None
    url: Optional[str] = None
    posted_at: Optional[datetime] = None
    relevance_score: Optional[int] = None
    opportunity_rank: Optional[int] = None
    status: Literal["new", "drafted", "approved", "rejected", "posted", "skipped"] = "new"
    created_at: Optional[datetime] = None


class CommentDraft(BaseModel):
    id: Optional[int] = None
    thread_id: str
    draft_text: str
    similarity_score: Optional[float] = None
    safety_flags: Optional[dict[str, Any]] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    edited_text: Optional[str] = None
    posted_at: Optional[datetime] = None
    reddit_comment_id: Optional[str] = None
    created_at: Optional[datetime] = None


class PostHistory(BaseModel):
    id: Optional[int] = None
    subreddit: str
    comment_text: str
    thread_url: Optional[str] = None
    karma_at_post: Optional[int] = None
    created_at: Optional[datetime] = None


class AnalyticsSnapshot(BaseModel):
    id: Optional[int] = None
    week_start: Optional[datetime] = None
    account_karma: Optional[int] = None
    total_impressions: Optional[int] = None
    llm_traffic: Optional[int] = None
    reddit_referral_traffic: Optional[int] = None
    organic_mentions: Optional[int] = None
    self_reported_leads: Optional[int] = None
    comments_posted: Optional[int] = None
    threads_posted: Optional[int] = None
    created_at: Optional[datetime] = None
