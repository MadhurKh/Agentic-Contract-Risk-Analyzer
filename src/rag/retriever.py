from __future__ import annotations

from typing import List
import math
import numpy as np

from .store import RagIndex, RagChunk


def _tokenize(text: str) -> List[str]:
    # lightweight tokenizer; aligns roughly with TfidfVectorizer's default token pattern
    import re
    return re.findall(r"[A-Za-z][A-Za-z0-9_]+", (text or "").lower())


def _build_query_vec(query: str, index: RagIndex) -> np.ndarray:
    tokens = _tokenize(query)
    if not tokens:
        return np.zeros((len(index.vocabulary),), dtype=np.float32)

    tf = {}
    for t in tokens:
        if t in index.vocabulary:
            tf[t] = tf.get(t, 0) + 1

    if not tf:
        return np.zeros((len(index.vocabulary),), dtype=np.float32)

    vec = np.zeros((len(index.vocabulary),), dtype=np.float32)
    for term, count in tf.items():
        j = index.vocabulary[term]
        # tf-idf with idf from training
        vec[j] = float(count) * float(index.idf[j])

    # L2 normalize
    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec = vec / norm
    return vec


def retrieve(
    *,
    query: str,
    index: RagIndex,
    top_k: int = 5,
) -> List[RagChunk]:
    """Cosine similarity over dense TF-IDF matrix."""
    if top_k <= 0 or index.tfidf_matrix.size == 0:
        return []

    q = _build_query_vec(query, index)
    if float(np.linalg.norm(q)) == 0:
        # fallback: return first chunks (avoids empty)
        return index.chunks[: min(top_k, len(index.chunks))]

    M = index.tfidf_matrix
    # Ensure row vectors are normalized: we normalized q, but matrix might not be.
    # We'll compute cosine = dot(q, row)/(||row||)
    dots = M @ q
    row_norms = np.linalg.norm(M, axis=1)
    sims = np.divide(dots, row_norms, out=np.zeros_like(dots), where=row_norms != 0)

    top_idx = np.argsort(-sims)[: min(top_k, len(index.chunks))]
    return [index.chunks[int(i)] for i in top_idx]
