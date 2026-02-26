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


def _normalize_jurisdiction(folder_name: str) -> str:
    """Map folder names to canonical jurisdiction codes used by the app.

    The UI and agents use jurisdictions like: EU, AU.
    If we store different values in the index metadata (e.g., EU_AI_ACT, AUSTRALIA),
    retrieval filters can return 0 results even though the index exists.
    """
    name = (folder_name or "").strip().lower()
    if name in {"eu", "europe", "european_union", "eu_ai_act", "eu-ai-act", "euaiact"}:
        return "EU"
    if name in {"au", "aus", "australia", "australian"}:
        return "AU"
    # Fallback: preserve something deterministic (but this may not match filters)
    return (folder_name or "").strip().upper() or "UNKNOWN"


def _discover_pdfs() -> list[dict]:
    pdfs: list[dict] = []
    if not REG_DIR.exists():
        return pdfs

    for juris_dir in REG_DIR.iterdir():
        if not juris_dir.is_dir():
            continue

        jurisdiction = _normalize_jurisdiction(juris_dir.name)

        for p in juris_dir.rglob("*.pdf"):
            # Use canonical jurisdiction code in doc_id to keep downstream logic simple.
            doc_id = f"{jurisdiction}-{p.stem}".replace(" ", "_")
            pdfs.append(
                {
                    "doc_id": doc_id,
                    "jurisdiction": jurisdiction,
                    "title": p.stem,
                    "filepath": str(p),
                }
            )

    return pdfs


def main() -> None:
    pdfs = _discover_pdfs()
    if not pdfs:
        print("No PDFs found.")
        print("Add PDFs under:")
        print("  data/regulations/eu_ai_act/")
        print("  data/regulations/australia/")
        return

    # Diagnostics: show canonical jurisdictions being used.
    juris_counts: dict[str, int] = {}
    for d in pdfs:
        juris_counts[d["jurisdiction"]] = juris_counts.get(d["jurisdiction"], 0) + 1

    print(f"Found {len(pdfs)} PDF(s). Jurisdiction split: {juris_counts}")
    print("Building TF-IDF RAG index...")

    index = build_index_from_pdfs(pdf_files=pdfs, chunk_size=1200, overlap=150)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_index(index, str(OUT_PATH))

    print(f"Saved index to {OUT_PATH}")
    print("IMPORTANT: If you changed jurisdictions or PDFs, restart Streamlit and re-run analysis.")


if __name__ == "__main__":
    main()
