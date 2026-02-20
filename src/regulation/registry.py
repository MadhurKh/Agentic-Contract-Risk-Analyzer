from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class RegulationSource:
    doc_id: str
    jurisdiction: str   # EU / AU
    title: str
    filepath: str       # local path (pdf) or extracted text path
    notes: str = ""


def default_sources() -> List[RegulationSource]:
    """Placeholder registry. We'll populate after you add PDFs."""
    return []
