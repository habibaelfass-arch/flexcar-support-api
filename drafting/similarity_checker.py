"""
Compares a new draft against past posted comments.
Flags drafts that are more than 40% similar to any prior post.
Uses TF-IDF cosine similarity (fast, no extra API call needed).
"""
from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MAX_SIMILARITY_SCORE = 0.40


def compute_max_similarity(draft: str, past_comments: list[str]) -> float:
    """
    Return the highest cosine similarity between `draft` and any item in
    `past_comments`. Returns 0.0 if there are no past comments to compare.
    """
    if not past_comments:
        return 0.0

    corpus = past_comments + [draft]
    vectorizer = TfidfVectorizer().fit_transform(corpus)
    draft_vec = vectorizer[-1]
    past_vecs = vectorizer[:-1]

    similarities = cosine_similarity(draft_vec, past_vecs).flatten()
    return float(similarities.max())


def is_too_similar(draft: str, past_comments: list[str], threshold: float = MAX_SIMILARITY_SCORE) -> tuple[bool, float]:
    """Return (is_flagged, similarity_score)."""
    score = compute_max_similarity(draft, past_comments)
    return score > threshold, score
