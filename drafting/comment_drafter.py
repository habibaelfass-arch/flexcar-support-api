"""
Generates a draft comment for a given thread using Claude,
then runs it through all safety checks before saving.
"""
from __future__ import annotations

from drafting.prompt_templates import COMMENT_DRAFTER_SYSTEM_PROMPT
from drafting.similarity_checker import is_too_similar
from safety.link_stripper import strip_links
from safety.banned_terms import contains_banned_term


def draft_comment(thread: dict, claude_client, past_comments: list[str] | None = None) -> dict:
    """
    Returns a draft dict:
        draft_text: str
        similarity_score: float
        safety_flags: dict  (keys: banned_terms, links_stripped, too_similar)
        safe_to_queue: bool
    """
    thread_content = f"Title: {thread['title']}\n\nBody: {thread['body']}"
    system_prompt = COMMENT_DRAFTER_SYSTEM_PROMPT.replace("[THREAD CONTENT]", thread_content)

    message = claude_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        system=system_prompt,
        messages=[{"role": "user", "content": "Write the comment now."}],
    )

    raw_draft = message.content[0].text.strip()

    # --- Safety passes ---
    links_stripped = False
    if strip_links(raw_draft) != raw_draft:
        raw_draft = strip_links(raw_draft)
        links_stripped = True

    banned_found, matched_terms = contains_banned_term(raw_draft)

    similarity_flagged, similarity_score = is_too_similar(raw_draft, past_comments or [])

    safety_flags = {
        "links_stripped": links_stripped,
        "banned_terms": matched_terms,
        "too_similar": similarity_flagged,
    }

    safe_to_queue = not banned_found and not similarity_flagged

    print(
        f"[drafter] r/{thread['subreddit']} | safe={safe_to_queue} | "
        f"similarity={similarity_score:.2f} | flags={safety_flags}"
    )

    return {
        "thread_id": thread.get("reddit_post_id"),
        "draft_text": raw_draft,
        "similarity_score": similarity_score,
        "safety_flags": safety_flags,
        "safe_to_queue": safe_to_queue,
    }
