from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from src.model_adapter import analyze_contract


@dataclass
class EvalCase:
    id: str
    title: str
    text: str
    expected_risk_level: str
    expected_categories: List[str]


def _normalize_level(level: str) -> str:
    return str(level).strip().title()


def _predicted_categories(result_dict: Dict[str, Any]) -> Set[str]:
    findings = result_dict.get("findings", [])
    cats = {f.get("category", "").strip() for f in findings if f.get("category")}
    return {c for c in cats if c}


def run_evaluation(cases: List[EvalCase]) -> Dict[str, Any]:
    """
    Runs evaluation cases through the adapter, compares predicted vs expected.

    Returns a dict:
    - risk_level_accuracy
    - category_precision/recall/f1 (micro)
    - mismatches[]
    """
    if not cases:
        return {
            "risk_level_accuracy": 0.0,
            "category_precision": 0.0,
            "category_recall": 0.0,
            "category_f1": 0.0,
            "mismatches": [],
            "n": 0,
        }

    level_hits = 0
    tp = fp = fn = 0
    mismatches: List[Dict[str, Any]] = []

    for c in cases:
        result = analyze_contract(c.text, title=c.title, source_type="paste").model_dump()

        pred_level = _normalize_level(result["summary"]["risk_level"])
        exp_level = _normalize_level(c.expected_risk_level)

        if pred_level == exp_level:
            level_hits += 1

        pred_cats = _predicted_categories(result)
        exp_cats = set(c.expected_categories)

        # micro counts
        tp += len(pred_cats & exp_cats)
        fp += len(pred_cats - exp_cats)
        fn += len(exp_cats - pred_cats)

        if pred_level != exp_level or pred_cats != exp_cats:
            mismatches.append(
                {
                    "id": c.id,
                    "title": c.title,
                    "pred_risk_level": pred_level,
                    "exp_risk_level": exp_level,
                    "pred_categories": sorted(list(pred_cats)),
                    "exp_categories": sorted(list(exp_cats)),
                    "run_id": result.get("run_id"),
                }
            )

    accuracy = level_hits / len(cases)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "risk_level_accuracy": round(accuracy, 3),
        "category_precision": round(precision, 3),
        "category_recall": round(recall, 3),
        "category_f1": round(f1, 3),
        "mismatches": mismatches,
        "n": len(cases),
    }


def load_cases(path: str | Path) -> List[EvalCase]:
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8"))

    cases: List[EvalCase] = []
    for row in payload:
        cases.append(
            EvalCase(
                id=row["id"],
                title=row.get("title", row["id"]),
                text=row["text"],
                expected_risk_level=row["expected_risk_level"],
                expected_categories=row.get("expected_categories", []),
            )
        )
    return cases


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Offline evaluation harness (stub).")
    parser.add_argument(
        "path",
        nargs="?",
        default="sample_data/eval_cases.json",
        help="Path to evaluation cases JSON (default: sample_data/eval_cases.json)",
    )
    args = parser.parse_args()

    cases = load_cases(args.path)
    metrics = run_evaluation(cases)

    print("\n=== Evaluation Summary ===")
    print(f"Cases: {metrics['n']}")
    print(f"Risk-level accuracy: {metrics['risk_level_accuracy']}")
    print(
        "Category micro P/R/F1: "
        f"{metrics['category_precision']} / {metrics['category_recall']} / {metrics['category_f1']}"
    )

    if metrics["mismatches"]:
        print("\n=== Mismatches ===")
        for m in metrics["mismatches"]:
            print(
                f"- {m['id']} | {m['title']} | "
                f"level {m['pred_risk_level']} vs {m['exp_risk_level']} | "
                f"cats {m['pred_categories']} vs {m['exp_categories']}"
            )
    else:
        print("\nNo mismatches 🎉")


if __name__ == "__main__":
    main()