"""
Ranks a batch of scored threads and filters out low-relevance ones.
"""
from __future__ import annotations

from scoring.relevance_scorer import RELEVANCE_THRESHOLD


def rank_and_filter(threads: list[dict], threshold: int = RELEVANCE_THRESHOLD) -> list[dict]:
    """
    1. Filter out threads below the relevance threshold.
    2. Sort remaining threads by relevance_score descending.
    3. Attach opportunity_rank (1 = best).
    """
    qualified = [t for t in threads if t.get("relevance_score", 0) >= threshold]
    qualified.sort(key=lambda t: t["relevance_score"], reverse=True)

    for rank, thread in enumerate(qualified, start=1):
        thread["opportunity_rank"] = rank

    skipped = len(threads) - len(qualified)
    print(f"[ranker] {len(qualified)} qualified, {skipped} skipped (below {threshold})")
    return qualified
