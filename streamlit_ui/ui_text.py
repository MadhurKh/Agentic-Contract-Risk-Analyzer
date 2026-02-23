"""
UI text helpers for Streamlit rendering.

Goal: avoid broken / chopped words in Executive Scorecard + Top Risks and keep
summaries consistent across the app.

IMPORTANT:
- Always truncate on word boundaries when possible.
- Always add an ellipsis when truncated.
- Strip trailing punctuation/quotes introduced by truncation.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Optional


_WS_RE = re.compile(r"\s+", re.UNICODE)


def normalize(text: str) -> str:
    """Collapse whitespace and trim."""
    if text is None:
        return ""
    return _WS_RE.sub(" ", str(text)).strip()


def _strip_trailing_junk(s: str) -> str:
    # Remove dangling punctuation that looks bad before an ellipsis.
    return s.rstrip(" ,;:-—–/\\|").rstrip()


def truncate(text: str, max_len: int = 90, ellipsis: str = "…") -> str:
    """
    Truncate without chopping mid-word; add ellipsis when truncated.

    If no word boundary is available (very long token), falls back to hard cut.
    """
    t = normalize(text)
    if not t:
        return ""
    if max_len <= 0:
        return ""
    if len(t) <= max_len:
        return t

    # Try to cut at a word boundary close to max_len
    window = t[: max_len + 1]
    cut = window.rfind(" ")
    # If cut is too far back, do a hard cut (handles long single-word cases)
    if cut < int(max_len * 0.6):
        cut = max_len

    out = window[:cut]
    out = _strip_trailing_junk(out)

    # Avoid leaving an unmatched quote due to truncation
    if out.count("'") % 2 == 1:
        out = out.rstrip("'").rstrip()
    if out.count('"') % 2 == 1:
        out = out.rstrip('"').rstrip()

    return out + ellipsis


def join_phrases(
    phrases: Iterable[str],
    *,
    max_items: int = 3,
    max_len_each: int = 70,
    sep: str = ", ",
) -> str:
    """
    Join a list of phrases into a compact string with safe truncation.
    """
    cleaned: List[str] = []
    for p in phrases:
        p2 = normalize(p)
        if not p2:
            continue
        cleaned.append(truncate(p2, max_len=max_len_each))
        if len(cleaned) >= max_items:
            break
    return sep.join(cleaned)


def safe_list(
    phrases: Iterable[str],
    *,
    max_items: int = 5,
    max_len_each: int = 90,
) -> List[str]:
    """
    Return a list of safely truncated phrases (for bullet lists).
    """
    out: List[str] = []
    for p in phrases:
        p2 = normalize(p)
        if not p2:
            continue
        out.append(truncate(p2, max_len=max_len_each))
        if len(out) >= max_items:
            break
    return out
