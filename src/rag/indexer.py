from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple
import os
import pickle

import numpy as np
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer

from .chunking import chunk_pages
from .store import RagChunk, RagIndex


def _read_pdf_pages(filepath: str) -> List[Tuple[int, str]]:
    reader = PdfReader(filepath)
    pages: List[Tuple[int, str]] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        pages.append((i, txt))
    return pages


def build_index_from_pdfs(
    *,
    pdf_files: List[Dict[str, Any]],
    chunk_size: int = 1200,
    overlap: int = 150,
    max_features: int = 60000,
) -> RagIndex:
    """
    Build a local TF-IDF index from a list of PDFs.

    pdf_files: list of dicts:
      {doc_id: str, jurisdiction: str, title: str, filepath: str}
    """
    chunks: List[RagChunk] = []

    for doc in pdf_files:
        doc_id = doc["doc_id"]
        fp = doc["filepath"]
        pages = _read_pdf_pages(fp)
        page_chunks = chunk_pages(pages, chunk_size=chunk_size, overlap=overlap)
        for j, (page_no, text) in enumerate(page_chunks, start=1):
            chunks.append(
                RagChunk(
                    chunk_id=f"{doc_id}::P{page_no:04d}::CH{j:04d}",
                    doc_id=doc_id,
                    text=text,
                    meta={
                        "jurisdiction": doc.get("jurisdiction", ""),
                        "title": doc.get("title", ""),
                        "filepath": fp,
                        "page": page_no,
                    },
                )
            )

    corpus = [c.text for c in chunks]
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        max_features=max_features,
        ngram_range=(1, 2),
    )
    tfidf = vectorizer.fit_transform(corpus)  # sparse
    tfidf_matrix = tfidf.astype(np.float32).toarray()

    vocab = dict(vectorizer.vocabulary_)
    idf = vectorizer.idf_.astype(np.float32)

    return RagIndex(chunks=chunks, vocabulary=vocab, idf=idf, tfidf_matrix=tfidf_matrix)


def save_index(index: RagIndex, filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        pickle.dump(index, f)


def load_index(filepath: str) -> RagIndex:
    with open(filepath, "rb") as f:
        return pickle.load(f)
