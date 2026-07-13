"""
GET  /queue          — list pending drafts for Sydney's approval
POST /approve/{id}   — approve (optionally with edited text)
POST /reject/{id}    — reject and delete draft
POST /mark-posted/{id} — Sydney confirms she posted it manually
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database.supabase_client import get_supabase_client
from database import queries

router = APIRouter(prefix="/queue", tags=["queue"])


class ApproveRequest(BaseModel):
    approved_by: str = "sydney"
    edited_text: Optional[str] = None


class MarkPostedRequest(BaseModel):
    reddit_comment_id: str


@router.get("")
def get_queue():
    """Returns all pending (unapproved) drafts with their thread context."""
    client = get_supabase_client()
    drafts = queries.get_pending_drafts(client)
    return {"drafts": drafts, "count": len(drafts)}


@router.post("/approve/{draft_id}")
def approve_draft(draft_id: int, body: ApproveRequest):
    client = get_supabase_client()
    queries.approve_draft(client, draft_id, body.approved_by, body.edited_text)
    return {"status": "approved", "draft_id": draft_id}


@router.post("/reject/{draft_id}")
def reject_draft(draft_id: int):
    client = get_supabase_client()
    queries.reject_draft(client, draft_id)
    return {"status": "rejected", "draft_id": draft_id}


@router.post("/mark-posted/{draft_id}")
def mark_posted(draft_id: int, body: MarkPostedRequest):
    """Sydney marks a draft as posted after she manually copies it to Reddit."""
    client = get_supabase_client()
    queries.mark_draft_posted(client, draft_id, body.reddit_comment_id)
    return {"status": "posted", "draft_id": draft_id}
