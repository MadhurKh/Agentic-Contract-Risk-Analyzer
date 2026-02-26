"""UI text helpers (safe truncation + light normalization).

Goals:
- Never truncate mid-word.
- Avoid leaving dangling punctuation like a trailing comma.
- Provide a consistent ellipsis character.

This module is intentionally dependency-free.
"""

from __future__ import annotations

import re
from typing import Optional

ELLIPSIS = "…"


def _strip_trailing_punct(s: str) -> str:
    # Remove trailing punctuation/spaces that make truncated text look broken.
    return re.sub(r"[\s,;:\-–—\(\[\{\"\']+$", "", s).strip()


def safe_truncate(text: Optional[str], max_chars: int, *, ellipsis: str = ELLIPSIS) -> str:
    """Truncate at a word boundary.

    If truncation happens, appends an ellipsis (default: …).
    """

    if not text:
        return ""

    t = str(text).strip()
    if max_chars <= 0:
        return ""

    if len(t) <= max_chars:
        return t

    # Reserve space for ellipsis
    cut = max(1, max_chars - len(ellipsis))
    candidate = t[:cut]

    # Prefer breaking at whitespace
    last_space = candidate.rfind(" ")
    if last_space >= max(10, int(cut * 0.6)):
        candidate = candidate[:last_space]

    candidate = _strip_trailing_punct(candidate)

    # If stripping made it too short (e.g., single long token), fall back to hard cut
    if len(candidate) < max(5, int(cut * 0.4)):
        candidate = _strip_trailing_punct(t[:cut])

    return f"{candidate}{ellipsis}"


def normalize_space(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def strip_wrapping_quotes(text: Optional[str]) -> str:
    """Remove wrapping single/double quotes if present."""
    if not text:
        return ""
    t = str(text).strip()
    if (t.startswith("'") and t.endswith("'")) or (t.startswith('"') and t.endswith('"')):
        return t[1:-1].strip()
    return t
