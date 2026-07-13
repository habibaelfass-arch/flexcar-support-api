"""
Hard list of prohibited words/phrases that must never appear in a posted comment.
"""

BANNED_TERMS: list[str] = [
    "car subscription",
    "no long-term commitment",
    "smarter way to own",
    "no tricks",
    "rideshare",
    "uber",
    "lyft",
    "flexcar.com",
    "http://",
    "https://",
]


def contains_banned_term(text: str) -> tuple[bool, list[str]]:
    """Return (found, list_of_matched_terms)."""
    text_lower = text.lower()
    matched = [term for term in BANNED_TERMS if term.lower() in text_lower]
    return bool(matched), matched
