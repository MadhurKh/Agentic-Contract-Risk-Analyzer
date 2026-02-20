from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ._common import AgentResult


@dataclass
class ReviewerConfig:
    """Configuration for executive scorecard agent."""
    mode: str = "deterministic"  # deterministic | llm


_SEV_WEIGHT = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def run_reviewer(*, verified_findings: List[Dict[str, Any]], config: Optional[ReviewerConfig] = None) -> AgentResult:
    """
    Agent 5 — Reviewer (Exec Scorecard) — deterministic MVP.
    """
    cfg = config or ReviewerConfig()

    total = len(verified_findings)
    needs_review = [f for f in verified_findings if f.get("status") == "NEEDS_REVIEW"]
    verified = [f for f in verified_findings if f.get("status") == "VERIFIED"]

    def sev_score(f: Dict[str, Any]) -> int:
        return _SEV_WEIGHT.get(str(f.get("severity", "MEDIUM")).upper(), 2)

    risk_points = sum(sev_score(f) for f in verified_findings)
    # scale to 0-100 (simple heuristic)
    overall = max(0, 100 - risk_points * 4 - len(needs_review) * 10)

    if overall >= 80:
        level = "LOW"
    elif overall >= 60:
        level = "MEDIUM"
    elif overall >= 40:
        level = "HIGH"
    else:
        level = "CRITICAL"

    top_sorted = sorted(verified_findings, key=lambda f: (sev_score(f), float(f.get("confidence", 0))), reverse=True)
    top_risks = [
        {
            "finding_id": f.get("finding_id"),
            "severity": f.get("severity"),
            "title": str(f.get("gap_statement", ""))[:120],
            "status": f.get("status"),
        }
        for f in top_sorted[:5]
    ]

    scorecard = {
        "overall_score": int(overall),
        "risk_level": level,
        "counts": {
            "total": total,
            "verified": len(verified),
            "needs_review": len(needs_review),
        },
        "top_risks": top_risks,
        "recommended_next_steps": [
            "Confirm jurisdiction scope (EU / AU) and applicable obligations.",
            "Upload regulation PDFs and build RAG index for grounded citations.",
            "Review NEEDS_REVIEW items: add missing evidence/citations and rerun.",
        ],
        "disclaimer": "This tool provides an assistive risk review and is not legal advice.",
    }

    warnings: List[str] = []
    if needs_review:
        warnings.append("Some findings need human review due to missing citations or low confidence.")

    return AgentResult(data={"risk_scorecard": scorecard, "mode": cfg.mode}, warnings=warnings)
