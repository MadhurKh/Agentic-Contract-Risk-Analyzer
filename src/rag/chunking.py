from __future__ import annotations

from typing import List, Tuple


def simple_chunk(text: str, *, chunk_size: int = 1200, overlap: int = 150) -> List[str]:
    """Simple character-based chunker (dependency-free)."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    chunks: List[str] = []
    i = 0
    n = len(text)
    step = max(1, chunk_size - overlap)
    while i < n:
        chunks.append(text[i:i+chunk_size])
        i += step
    return chunks


def chunk_pages(pages: List[Tuple[int, str]], *, chunk_size: int = 1200, overlap: int = 150) -> List[Tuple[int, str]]:
    """
    Chunk page texts while preserving page number in the output.
    Returns list of (page_no, chunk_text).
    """
    out: List[Tuple[int, str]] = []
    for page_no, text in pages:
        for ch in simple_chunk(text or "", chunk_size=chunk_size, overlap=overlap):
            if ch.strip():
                out.append((page_no, ch))
    return out
