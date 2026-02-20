from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is on sys.path when running as `python scripts/build_reg_index.py`
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.rag.indexer import build_index_from_pdfs, save_index  # noqa: E402


REG_DIR = REPO_ROOT / "data" / "regulations"
OUT_PATH = REPO_ROOT / "data" / "rag_index" / "reg_index.pkl"


def _discover_pdfs() -> list[dict]:
    pdfs: list[dict] = []
    if not REG_DIR.exists():
        return pdfs

    for juris_dir in REG_DIR.iterdir():
        if not juris_dir.is_dir():
            continue
        jurisdiction = juris_dir.name.upper()
        for p in juris_dir.rglob("*.pdf"):
            doc_id = f"{jurisdiction}-{p.stem}".replace(" ", "_")
            pdfs.append({
                "doc_id": doc_id,
                "jurisdiction": jurisdiction,
                "title": p.stem,
                "filepath": str(p),
            })
    return pdfs


def main() -> None:
    pdfs = _discover_pdfs()
    if not pdfs:
        print("No PDFs found.")
        print("Add PDFs under:")
        print("  data/regulations/eu_ai_act/")
        print("  data/regulations/australia/")
        return

    print(f"Found {len(pdfs)} PDF(s). Building TF-IDF RAG index...")
    index = build_index_from_pdfs(pdf_files=pdfs, chunk_size=1200, overlap=150)
    save_index(index, str(OUT_PATH))
    print(f"Saved index to {OUT_PATH}")


if __name__ == "__main__":
    main()
