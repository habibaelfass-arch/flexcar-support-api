"""
Removes any URLs from draft comments before they are surfaced for approval.
flexcar_sam should never post links per the safety config.
"""
from __future__ import annotations

import re

URL_PATTERN = re.compile(
    r"https?://\S+|www\.\S+",
    re.IGNORECASE,
)


def strip_links(text: str) -> str:
    """Remove all URLs from text."""
    cleaned = URL_PATTERN.sub("", text)
    # Collapse extra whitespace left behind
    cleaned = re.sub(r" {2,}", " ", cleaned).strip()
    return cleaned


def has_links(text: str) -> bool:
    return bool(URL_PATTERN.search(text))
