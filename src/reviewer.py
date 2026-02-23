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
    s = (sev or "MEDIUM").upper().strip()
    return _SEV_W.get(s, 2)


def _risk_level(score: float) -> str:
    if score >= 3.4:
        return "CRITICAL"
    if score >= 2.7:
        return "HIGH"
    if score >= 1.8:
        return "MEDIUM"
    return "LOW"



def _truncate_text(text: str, max_len: int = 90) -> str:
    """Truncate without chopping mid-word; add ellipsis when truncated."""
    t = " ".join((text or "").split()).strip()
    if not t:
        return ""
    if len(t) <= max_len:
        return t
    # Try to cut at a word boundary close to max_len
    window = t[: max_len + 1]
    cut = window.rfind(" ")
    if cut < int(max_len * 0.6):
        cut = max_len
    t2 = window[:cut].rstrip(" ,;:-")
    return t2 + "…"

def _summarize_title(f: Dict[str, Any]) -> str:
    gap = str(f.get("gap_statement") or f.get("risk_statement") or "").strip()
    if not gap:
        return "Regulatory gap identified"
    return _truncate_text(gap, max_len=90)


def _group_by_clause(findings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    g: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for f in findings:
        cid = str(f.get("clause_id") or "UNKNOWN")
        g[cid].append(f)
    return g


def _compound_risk_rules(by_clause: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    compounds: List[Dict[str, Any]] = []

    def add(rule_id: str, title: str, rationale: str, severity: str):
        compounds.append(
            {"rule_id": rule_id, "title": title, "rationale": rationale, "severity": severity}
        )

    has_security = any(
        (f.get("tags") or []) and ("cybersecurity" in (f.get("tags") or []) or "security_controls" in (f.get("tags") or []))
        for fs in by_clause.values()
        for f in fs
    )
    has_logging = any(
        (f.get("tags") or []) and ("logging" in (f.get("tags") or []) or "traceability" in (f.get("tags") or []))
        for fs in by_clause.values()
        for f in fs
    )
    has_priv = any(
        (f.get("tags") or []) and ("privacy" in (f.get("tags") or []) or "data_governance" in (f.get("tags") or []))
        for fs in by_clause.values()
        for f in fs
    )
    has_human = any(
        (f.get("tags") or []) and ("human_oversight" in (f.get("tags") or []) or "controls" in (f.get("tags") or []))
        for fs in by_clause.values()
        for f in fs
    )

    clause_types = set()
    for fs in by_clause.values():
        for f in fs:
            ct = (f.get("clause_type") or "").upper().strip()
            if ct:
                clause_types.add(ct)

    if has_security and has_logging:
        add(
            "CR-CONTROLS-01",
            "Security controls without traceability increases audit/regulatory exposure",
            "Combined gaps across security and logging reduce ability to demonstrate compliance and investigate incidents.",
            "HIGH",
        )

    if has_priv and has_security:
        add(
            "CR-DATA-01",
            "Data handling risk elevated due to combined privacy + security gaps",
            "Weaknesses in privacy and security clauses increase likelihood of non-compliance and breach impact.",
            "HIGH",
        )

    if has_human and ("MODEL_RISK" in clause_types or "GOVERNANCE" in clause_types):
        add(
            "CR-OPS-01",
            "Operational risk: inadequate oversight combined with model governance gaps",
            "Without oversight and governance guardrails, model failures may go undetected or unmanaged.",
            "MEDIUM",
        )

    return compounds


def run_reviewer(*, verified_findings: List[Dict[str, Any]], config: Optional[ReviewerConfig] = None) -> AgentResult:
    cfg = config or ReviewerConfig()

    if not verified_findings:
        return AgentResult(
            data={
                "risk_scorecard": {
                    "overall_score": 0.0,
                    "risk_level": "LOW",
                    "counts": {},
                    "top_risks": [],
                    "compound_risks": [],
                    "recommended_next_steps": [],
                    "executive_summary": "",
                    "disclaimer": "This output is for demonstration only and does not constitute legal advice.",
                }
            }
        )

    by_clause = _group_by_clause(verified_findings)

    sev_vals = [_sev_weight(f.get("severity", "MEDIUM")) for f in verified_findings]
    overall_score = round(sum(sev_vals) / max(1, len(sev_vals)), 2)
    risk_level = _risk_level(overall_score)

    counts = {"total": len(verified_findings), "verified": 0, "needs_review": 0, "draft": 0}
    for f in verified_findings:
        st = str(f.get("status", "")).upper().strip()
        if st == "VERIFIED":
            counts["verified"] += 1
        elif st == "NEEDS_REVIEW":
            counts["needs_review"] += 1
        else:
            counts["draft"] += 1

    def rank_key(f: Dict[str, Any]):
        sev = _sev_weight(f.get("severity", "MEDIUM"))
        conf = float(f.get("confidence", 0.0))
        has_cit = 1 if (f.get("reg_citations") or []) else 0
        return (sev, conf, has_cit)

    top = sorted(verified_findings, key=rank_key, reverse=True)[: cfg.top_risks]
    top_risks = [
        {"severity": (f.get("severity") or "MEDIUM"), "title": _summarize_title(f), "finding_id": f.get("finding_id")}
        for f in top
    ]

    compound = _compound_risk_rules(by_clause)

    recommended: List[str] = []
    if counts["needs_review"] > 0:
        recommended.append("Resolve NEEDS_REVIEW items by adding missing regulatory citations and explicit contractual commitments.")
    recommended.append("Confirm applicability scope (high-risk vs limited-risk) and align contract commitments to that classification.")
    recommended.append("Add measurable controls: logging retention, audit rights, human oversight escalation paths, and incident notification SLAs.")
    if risk_level in {"HIGH", "CRITICAL"}:
        recommended.append("Escalate to legal/compliance for a targeted review of the highest severity findings.")

    exec_summary = (
        f"Risk level is {risk_level} (score {overall_score}). "
        f"{counts['needs_review']} items require additional grounding/citations before conclusions can be finalized. "
        f"Top exposure areas include: " + ", ".join([r['title'] for r in top_risks[:3]]) + "."
    )
    if compound:
        exec_summary += " Notable compound risks were detected (controls interplay), indicating elevated exposure beyond individual clause gaps."

    return AgentResult(
        data={
            "risk_scorecard": {
                "overall_score": overall_score,
                "risk_level": risk_level,
                "counts": counts,
                "top_risks": top_risks,
                "compound_risks": compound,
                "recommended_next_steps": recommended,
                "executive_summary": exec_summary,
                "disclaimer": "This output is for demonstration only and does not constitute legal advice.",
            }
        }
    )
