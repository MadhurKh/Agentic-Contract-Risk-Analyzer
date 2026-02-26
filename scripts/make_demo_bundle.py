"""Create a shareable demo bundle without committing local PDFs or indexes.

Outputs:
- demo_bundle/
  - latest_demo_run.json (copied from outputs/)
  - DEMO_SCRIPT.md
  - ARCHITECTURE.md
  - LOCAL_PDF_ONLY.md

Usage:
  python scripts/make_demo_bundle.py
"""
from __future__ import annotations

import shutil
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "demo_bundle"
OUTPUTS_DIR = REPO_ROOT / "outputs"

def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    latest = OUTPUTS_DIR / "latest_demo_run.json"
    if not latest.exists():
        print(f"[ERROR] Missing: {latest}")
        print("Run run_export_demo.bat first.")
        return 2

    shutil.copy2(latest, OUT_DIR / "latest_demo_run.json")

    docs = REPO_ROOT / "docs"
    for name in ["DEMO_SCRIPT.md", "ARCHITECTURE.md", "LOCAL_PDF_ONLY.md"]:
        src = docs / name
        if src.exists():
            shutil.copy2(src, OUT_DIR / name)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    marker = OUT_DIR / f"BUNDLE_CREATED_{stamp}.txt"
    marker.write_text("Demo bundle created. Do not include local PDFs or rag_index in commits.\n", encoding="utf-8")

    print(f"[OK] Demo bundle created: {OUT_DIR}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
