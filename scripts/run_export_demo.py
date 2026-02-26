from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Ensure repo root is on sys.path
THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.model_adapter import analyze_contract  # noqa: E402


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _dump_jsonable(obj: Any) -> Any:
    # Pydantic v2: model_dump
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    # Pydantic v1: dict
    if hasattr(obj, "dict"):
        return obj.dict()
    # dataclasses / plain
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return obj


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run headless contract analysis export.")
    ap.add_argument("--input", type=str, default="", help="Path to input .txt contract")
    ap.add_argument("--sample", action="store_true", help="Use sample_data/sample_contract_large.txt")
    ap.add_argument("--agentic", action="store_true", help="Enable agentic mode")
    ap.add_argument("--require-citations", action="store_true", help="Require local regulation citations")
    ap.add_argument("--jurisdictions", nargs="*", default=["EU", "AU"], help="Jurisdictions (EU, AU)")
    ap.add_argument("--out", type=str, default="outputs/latest_demo_run.json", help="Output JSON path")
    args = ap.parse_args(argv)

    outputs_dir = REPO_ROOT / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    out_path = (REPO_ROOT / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out).resolve()
    _ensure_parent(out_path)

    # Determine input
    if args.sample or (not args.input):
        input_path = REPO_ROOT / "sample_data" / "sample_contract_large.txt"
    else:
        input_path = Path(args.input).expanduser()
        if not input_path.is_absolute():
            input_path = (REPO_ROOT / input_path).resolve()

    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}", flush=True)
        return 2

    contract_text = _read_text(input_path)
    title = input_path.name

    # Run analysis
    result = analyze_contract(
        contract_text=contract_text,
        title=title,
        source_type="paste",
        agentic_mode=bool(args.agentic),
        require_reg_citations=bool(args.require_citations),
        jurisdictions=list(args.jurisdictions or []),
    )

    payload = _dump_jsonable(result)

    # Always also save a timestamped copy alongside latest
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ts_path = outputs_dir / f"demo_run_{ts}.json"

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    with ts_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[OK] Repo root: {REPO_ROOT}", flush=True)
    print(f"[OK] Input: {input_path}", flush=True)
    print(f"[OK] Wrote: {out_path}", flush=True)
    print(f"[OK] Wrote: {ts_path}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        # Write a friendly error file under outputs
        outputs_dir = (REPO_ROOT / "outputs")
        outputs_dir.mkdir(parents=True, exist_ok=True)
        err_path = outputs_dir / "export_error.txt"
        tb = traceback.format_exc()
        with err_path.open("w", encoding="utf-8") as f:
            f.write(tb)
        print("[ERROR] Export crashed. See outputs/export_error.txt", flush=True)
        raise
