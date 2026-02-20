from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class RagChunk:
    chunk_id: str
    doc_id: str
    text: str
    meta: Dict[str, Any]


@dataclass
class RagIndex:
    """Lightweight local RAG index based on TF-IDF."""
    chunks: List[RagChunk]
    vocabulary: Dict[str, int]
    idf: np.ndarray
    tfidf_matrix: np.ndarray  # shape: (n_chunks, n_terms)

