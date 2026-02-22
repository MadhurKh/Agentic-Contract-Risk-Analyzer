from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from collections import defaultdict

from ._common import AgentResult


@dataclass
class ReviewerConfig:
    mode: str = "deterministic"
    top_risks: int = 5


_SEV_W = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def _sev_weight(sev: str) -> int:
    s = (sev or "MEDIUM").upper()
    return _SEV_W.get(s, 2)


def _risk_level_from_score(score_0_100: int) -> str:
    if score_0_100 >= 85:
        return "CRITICAL"
    if score_0_100 >= 65:
        return "HIGH"
    if score_0_100 >= 35:
        return "MEDIUM"
    return "LOW"


def run_reviewer(*, verified_findings: List[Dict[str, Any]], config: Optional[ReviewerConfig] = None) -> AgentResult:
    """Summarizes findings into an executive scorecard.

    IMPORTANT: We keep the executive summary's displayed score aligned with the scorecard score
    to avoid UI mismatches (e.g., headline score vs scorecard score).
    """
    cfg = config or ReviewerConfig()

    findings = verified_findings or []
    counts = {"verified": 0, "needs_review": 0}

    # Compute an interpretable 0-100 score:
    # - each finding contributes (severity_weight/4) * confidence
    # - NEEDS_REVIEW findings are included but penalized via (0.85 multiplier)
    # - normalize by max possible per finding (=1.0) to get 0..100
    total = 0.0
    denom = 0.0
    sev_sum = 0.0
    sev_n = 0

    for f in findings:
        status = (f.get("status") or "NEEDS_REVIEW").upper()
        if status == "VERIFIED":
            counts["verified"] += 1
            status_mult = 1.0
        else:
            counts["needs_review"] += 1
            status_mult = 0.85  # small penalty to reflect uncertainty

        conf = float(f.get("confidence", 0.6) or 0.6)
        conf = max(0.0, min(1.0, conf))

        sev_w = _sev_weight(str(f.get("severity", "MEDIUM")))
        sev_sum += sev_w
        sev_n += 1

        contrib = (sev_w / 4.0) * conf * status_mult
        total += contrib
        denom += 1.0  # max contrib per finding is 1.0

    score_0_100 = int(round((total / denom) * 100)) if denom else 0
    risk_level = _risk_level_from_score(score_0_100)
    avg_sev = (sev_sum / sev_n) if sev_n else 0.0

    # Top risks: highest severity first, then confidence
    def _sort_key(x: Dict[str, Any]):
        return (_sev_weight(str(x.get("severity", "MEDIUM"))), float(x.get("confidence", 0.0) or 0.0))

    ranked = sorted(findings, key=_sort_key, reverse=True)
    top_risks = ranked[: cfg.top_risks]

    # Compound risks (simple heuristic)
    compound: List[Dict[str, Any]] = []
    cats = defaultdict(int)
    for f in findings:
        cat = (f.get("category") or "General")
        cats[str(cat)] += 1
    if cats.get("Security", 0) and cats.get("Privacy", 0):
        compound.append({
            "severity": "HIGH",
            "title": "Data handling risk elevated due to combined privacy + security gaps",
            "description": "Weaknesses in privacy and security clauses increase likelihood of non-compliance and breach impact.",
        })
    if cats.get("Logging", 0) and cats.get("Security", 0):
        compound.append({
            "severity": "HIGH",
            "title": "Security controls without traceability increases audit/regulatory exposure",
            "description": "Combined gaps across security and logging reduce ability to demonstrate compliance and investigate incidents.",
        })

    recommended = []
    if counts["needs_review"] > 0:
        recommended.append("Resolve NEEDS_REVIEW items by adding missing regulatory citations and explicit contractual commitments.")
    recommended.append("Confirm applicability scope (high-risk vs limited-risk) and align contract commitments to that classification.")
    recommended.append("Add measurable controls: logging retention, audit rights, human oversight escalation paths, and incident notification SLAs.")

    # Executive summary: MUST reference the SAME score shown in scorecard score.
    exec_summary = (
        f"Risk level is {risk_level} (score {float(score_0_100):.1f}/100; avg severity {avg_sev:.2f}/4). "
        f"{counts['needs_review']} items require additional grounding/citations before conclusions can be finalized. "
        f"Top exposure areas include: " + ", ".join([r.get('title', 'Risk') for r in top_risks[:3]]) + "."
    )
    if compound:
        exec_summary += " Notable compound risks were detected (controls interplay), indicating elevated exposure beyond individual clause gaps."

    return AgentResult(
        data={
            "risk_scorecard": {
                # canonical
                "overall_score_0_100": score_0_100,
                "risk_level": risk_level,
                "counts": counts,
                "top_risks": top_risks,
                "compound_risks": compound,
                "recommended_next_steps": recommended,
                "executive_summary": exec_summary,

                # aliases for UI robustness
                "score": float(score_0_100),
                "overall_score": float(score_0_100),
            }
        }
    )
