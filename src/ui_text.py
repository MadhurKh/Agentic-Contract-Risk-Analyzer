from __future__ import annotations

import re

def _balance_quotes(s: str) -> str:
    # If odd count of single quotes, remove the last dangling quote segment
    if s.count("'") % 2 == 1:
        idx = s.rfind("'")
        if idx != -1:
            s = s[:idx].rstrip()
    return s

def safe_truncate(text: str, max_len: int, *, placeholder: str = "…") -> str:
    """Truncate at word boundary (never mid-word) and avoid dangling quotes.

    This is intended for UI display only.
    """
    t = (text or "").strip()
    if len(t) <= max_len:
        return t

    cut = t[:max_len].rstrip()

    # Backtrack to last whitespace boundary (avoid mid-word)
    m = re.search(r"\s+\S*$", cut)
    if m:
        cut = cut[: m.start()].rstrip()

    cut = _balance_quotes(cut)

    # Fallback hard cut if needed (e.g., single very long token)
    if not cut:
        cut = t[:max_len].rstrip()
        cut = _balance_quotes(cut)

    # Avoid ugly trailing punctuation
    cut = cut.rstrip(",;:-")
    return f"{cut}{placeholder}"

# Backward/alternate naming (if other modules import truncate)
def truncate(text: str, max_len: int, placeholder: str = "…") -> str:
    return safe_truncate(text, max_len, placeholder=placeholder)

def safe_list(items: list[str], *, max_items: int = 5, max_len_each: int = 90) -> list[str]:
    out = []
    for x in (items or [])[:max_items]:
        out.append(safe_truncate(str(x), max_len_each))
    return out

def join_phrases(items: list[str], *, max_items: int = 3, max_len_each: int = 70) -> str:
    parts = safe_list(items, max_items=max_items, max_len_each=max_len_each)
    return ", ".join([p for p in parts if p])
