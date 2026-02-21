from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np

from .store import RagIndex, RagChunk


def _tokenize(text: str) -> List[str]:
    import re
    return re.findall(r"[A-Za-z][A-Za-z0-9_]+", (text or "").lower())


def _build_query_vec(query: str, index: RagIndex) -> np.ndarray:
    tokens = _tokenize(query)
    if not tokens:
        return np.zeros((len(index.vocabulary),), dtype=np.float32)

    tf: Dict[str, int] = {}
    for t in tokens:
        if t in index.vocabulary:
            tf[t] = tf.get(t, 0) + 1

    if not tf:
        return np.zeros((len(index.vocabulary),), dtype=np.float32)

    vec = np.zeros((len(index.vocabulary),), dtype=np.float32)
    for term, count in tf.items():
        j = index.vocabulary[term]
        vec[j] = float(count) * float(index.idf[j])

    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec = vec / norm
    return vec


def retrieve(
    *,
    query: str,
    index: RagIndex,
    top_k: int = 5,
    filters: Optional[Dict[str, str]] = None,
) -> List[RagChunk]:
    """Cosine similarity over dense TF-IDF matrix with optional metadata filtering."""
    if top_k <= 0 or index.tfidf_matrix.size == 0:
        return []

    candidates = list(range(len(index.chunks)))
    if filters:
        juris = (filters.get("jurisdiction") or "").upper().strip()
        doc_prefix = filters.get("doc_prefix") or ""
        if juris:
            candidates = [i for i in candidates if str(index.chunks[i].meta.get("jurisdiction","")).upper() == juris]
        if doc_prefix:
            candidates = [i for i in candidates if str(index.chunks[i].doc_id).startswith(doc_prefix)]

    if not candidates:
        return []

    q = _build_query_vec(query, index)
    if float(np.linalg.norm(q)) == 0:
        return [index.chunks[i] for i in candidates[: min(top_k, len(candidates))]]

    M = index.tfidf_matrix[candidates, :]
    dots = M @ q
    row_norms = np.linalg.norm(M, axis=1)
    sims = np.divide(dots, row_norms, out=np.zeros_like(dots), where=row_norms != 0)

    top_local = np.argsort(-sims)[: min(top_k, len(candidates))]
    top_idx = [candidates[int(i)] for i in top_local]
    return [index.chunks[i] for i in top_idx]
