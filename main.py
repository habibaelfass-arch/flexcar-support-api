"""
Entry point — runs the full Reddit monitoring pipeline.
Called by GitHub Actions every 30 minutes.
"""
from __future__ import annotations

import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

from monitor.subreddit_watcher import fetch_recent_posts
from monitor.deduplicator import filter_new_threads
from monitor.rules_checker import check_subreddit_safety
from scoring.relevance_scorer import score_thread, passes_threshold
from scoring.opportunity_ranker import rank_and_filter
from safety.frequency_limiter import can_post_today, get_posts_today_from_db
from drafting.comment_drafter import draft_comment
from database.supabase_client import get_supabase_client
from database import queries


def run_pipeline() -> None:
    print("=" * 60)
    print("[pipeline] starting Reddit monitoring run")
    print("=" * 60)

    claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    db = get_supabase_client()

    # 1. FETCH
    threads = fetch_recent_posts()
    if not threads:
        print("[pipeline] no threads fetched — exiting")
        return

    # 2. DEDUPLICATE
    existing_ids = queries.get_existing_post_ids(db)
    threads = filter_new_threads(threads, db_seen_ids=existing_ids)
    if not threads:
        print("[pipeline] all threads already processed — exiting")
        return

    # 3. RULES CHECK — skip threads from red-rated subreddits
    safe_threads = []
    subreddit_ratings: dict[str, str] = {}
    for thread in threads:
        sub = thread["subreddit"]
        if sub not in subreddit_ratings:
            result = check_subreddit_safety(sub, claude_client=claude)
            subreddit_ratings[sub] = result["rating"]
        if subreddit_ratings[sub] == "red":
            print(f"[pipeline] skipping r/{sub} (RED rating)")
            queries.upsert_thread(db, {**thread, "status": "skipped"})
            continue
        safe_threads.append(thread)

    if not safe_threads:
        print("[pipeline] no threads passed rules check — exiting")
        return

    # 4. RELEVANCE SCORE
    scored = []
    for thread in safe_threads:
        thread = score_thread(thread, claude)
        scored.append(thread)

    # 5. FILTER + RANK
    ranked = rank_and_filter(scored)
    if not ranked:
        print("[pipeline] no threads passed relevance threshold — exiting")
        return

    # 6. FREQUENCY CHECK
    posts_today = get_posts_today_from_db(db)
    if not can_post_today(posts_today):
        print(f"[pipeline] daily cap reached ({posts_today} posts today) — saving threads, skipping drafts")
        for thread in ranked:
            queries.upsert_thread(db, {**thread, "status": "new"})
        return

    # 7. DRAFT + SAFETY PASS
    past_comments = queries.get_recent_comment_texts(db)

    drafts_queued = 0
    for thread in ranked:
        row = queries.upsert_thread(db, {**thread, "status": "drafted"})
        if not row:
            continue

        draft = draft_comment(thread, claude, past_comments=past_comments)

        if not draft["safe_to_queue"]:
            print(f"[pipeline] draft failed safety check for {thread['reddit_post_id']}: {draft['safety_flags']}")
            queries.update_thread_status(db, thread["reddit_post_id"], "skipped")
            continue

        # 8. SAVE TO SUPABASE
        queries.save_draft(db, draft, thread_db_id=row["id"])
        queries.update_thread_status(db, thread["reddit_post_id"], "drafted")
        drafts_queued += 1
        print(f"[pipeline] draft queued for r/{thread['subreddit']} — {thread['title'][:60]}")

    print("=" * 60)
    print(f"[pipeline] done — {drafts_queued} drafts queued for Sydney's review")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
