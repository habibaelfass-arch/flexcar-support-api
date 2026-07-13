"""
GET  /settings/subreddits        — list all monitored subreddits
POST /settings/subreddits        — add a new subreddit
DELETE /settings/subreddits/{name} — remove a subreddit
PATCH /settings/subreddits/{name}  — toggle active or trigger rules re-check
GET  /settings/config            — current keyword/threshold config
PATCH /settings/config           — update keyword list, threshold, daily cap
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database.supabase_client import get_supabase_client

router = APIRouter(prefix="/settings", tags=["settings"])


class AddSubredditRequest(BaseModel):
    name: str
    safety_rating: str = "yellow"


class PatchSubredditRequest(BaseModel):
    active: Optional[bool] = None
    recheck_rules: bool = False


_config: dict = {
    "relevance_threshold": 65,
    "max_posts_per_day": 3,
    "keywords": [
        "car lease", "month to month", "monthly car",
        "flexible lease", "car subscription", "hate my lease",
        "car payment too high", "stuck in lease",
        "need a car short term", "temporary car",
    ],
    "banned_terms": [
        "car subscription", "no long-term commitment",
        "smarter way to own", "no tricks", "rideshare", "uber", "lyft",
    ],
}


@router.get("/subreddits")
def list_subreddits():
    client = get_supabase_client()
    result = client.table("monitored_subreddits").select("*").order("name").execute()
    return {"subreddits": result.data or []}


@router.post("/subreddits")
def add_subreddit(body: AddSubredditRequest):
    client = get_supabase_client()
    result = (
        client.table("monitored_subreddits")
        .insert({"name": body.name, "safety_rating": body.safety_rating})
        .execute()
    )
    return {"created": result.data[0] if result.data else None}


@router.delete("/subreddits/{name}")
def remove_subreddit(name: str):
    client = get_supabase_client()
    client.table("monitored_subreddits").delete().eq("name", name).execute()
    return {"deleted": name}


@router.patch("/subreddits/{name}")
def patch_subreddit(name: str, body: PatchSubredditRequest):
    client = get_supabase_client()
    update: dict = {}
    if body.active is not None:
        update["active"] = body.active
    if update:
        client.table("monitored_subreddits").update(update).eq("name", name).execute()
    return {"updated": name, "changes": update}


@router.get("/config")
def get_config():
    return _config


@router.patch("/config")
def update_config(patch: dict):
    allowed_keys = {"relevance_threshold", "max_posts_per_day", "keywords", "banned_terms"}
    for key in patch:
        if key not in allowed_keys:
            raise HTTPException(status_code=400, detail=f"Unknown config key: {key}")
        _config[key] = patch[key]
    return _config
