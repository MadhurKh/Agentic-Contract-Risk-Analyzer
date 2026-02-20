from __future__ import annotations

import re
from typing import List

from .schemas import Feature, FeatureSet


def _has(pattern: str, text: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE) is not None


def extract_features(contract_text: str) -> FeatureSet:
    """
    Feature extraction boundary.
    Today: lightweight rule-based (portable, deterministic, testable).
    Tomorrow: replace with DS pipeline (NER/classification/embeddings) without changing UI.
    """
    t = contract_text or ""

    # Very simple “signals” that DS teams typically start with as binary flags + basic counts.
    features: List[Feature] = [
        Feature(name="text_length", value=len(t), dtype="int"),
        Feature(name="has_consequential_damages", value=_has(r"consequential damages", t), dtype="bool"),
        Feature(name="has_uncapped_liability", value=_has(r"(uncapped|unlimited)\s+liabilit", t), dtype="bool"),
        Feature(name="has_indemnity", value=_has(r"\bindemnif", t), dtype="bool"),
        Feature(name="has_termination_for_convenience", value=_has(r"terminate\s+for\s+convenience", t), dtype="bool"),
        Feature(name="has_cure_period", value=_has(r"\bcure\s+period\b|\b(\d+)\s+days?\s+to\s+cure\b", t), dtype="bool"),
        Feature(name="has_auto_renewal", value=_has(r"auto(?:matic)?\s+renew", t), dtype="bool"),
    ]

    return FeatureSet(features=features)