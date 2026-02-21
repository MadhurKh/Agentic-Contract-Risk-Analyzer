from __future__ import annotations

import re
from typing import Iterable, List, Set


_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]+")


def tokenize(text: str) -> List[str]:
    return _WORD_RE.findall((text or "").lower())


def keyword_set(text: str, *, stop: Set[str] | None = None) -> Set[str]:
    toks = set(tokenize(text))
    if stop:
        toks = {t for t in toks if t not in stop}
    return toks


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0
