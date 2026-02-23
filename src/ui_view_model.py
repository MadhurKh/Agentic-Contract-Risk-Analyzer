from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .schemas import AnalysisResult, Finding
from .ui_text import safe_truncate


@dataclass
class UIView:
    score_0_100: int
    risk_level: str
    verified_count: int
    needs_review_count: int
    exec_summary: str
    top_risks: List[Dict[str, Any]]
    findings: List[Finding]
    raw: AnalysisResult


def _safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(round(float(x)))
    except Exception:
        return default


def _safe_str(x: Any, default: str = "") -> str:
    return default if x is None else str(x)


def build_ui_view(result: AnalysisResult) -> UIView:
    """Build a UI-safe view model.

    Key guarantee: **no mid-word truncation** in any user-visible summary fields.
    """
    # Canonical scoring: prefer scoring breakdown, else summary.
    score = result.scoring.normalized_score_0_100 if result.scoring else result.summary.overall_risk_score
    risk_level = result.scoring.risk_level if result.scoring else result.summary.risk_level

    findings = result.findings or []

    verified = 0
    needs_review = 0
    for f in findings:
        st = (getattr(f, "status", None) or "").upper()
        if st == "VERIFIED":
            verified += 1
        elif st == "NEEDS_REVIEW":
            needs_review += 1

    # If status not populated, infer needs_review from presence of quality reasons or missing reg citations
    if verified == 0 and needs_review == 0 and findings:
        for f in findings:
            qr = getattr(f, "quality_reason_codes", []) or []
            rc = getattr(f, "reg_citations", []) or []
            if qr or not rc:
                needs_review += 1
            else:
                verified += 1

    # Top risks: prefer summary.top_risks but ensure text exists and truncate safely per item.
    top: List[Dict[str, Any]] = []
    if result.summary and result.summary.top_risks:
        for t in result.summary.top_risks[:5]:
            title = _safe_str(t.get("title") or t.get("risk") or t.get("statement") or "")
            cat = _safe_str(t.get("category") or t.get("cat") or "Risk")
            if title:
                top.append({"severity": t.get("severity"), "category": cat, "title": safe_truncate(title, 90)})
    if not top:
        # fallback from findings
        for f in findings[:5]:
            top.append({"severity": f.severity, "category": f.category, "title": safe_truncate(f.risk_statement, 90)})

    # Executive summary: build from canonical score + top risks + needs review
    top_titles = [t.get("title", "") for t in top[:3] if t.get("title")]
    top_str = ", ".join(top_titles) if top_titles else "key contract obligations"
    exec_summary = (
        f"Risk level is {str(risk_level).upper()} (score {float(score):.1f}/100). " 
        f"{needs_review} items require additional grounding/citations before conclusions can be finalized. "
        f"Top exposure areas include: {top_str}."
    )
    # Keep the paragraph tidy (never mid-word)
    exec_summary = safe_truncate(exec_summary, 260)

    return UIView(
        score_0_100=_safe_int(score),
        risk_level=_safe_str(risk_level),
        verified_count=verified,
        needs_review_count=needs_review,
        exec_summary=exec_summary,
        top_risks=top,
        findings=findings,
        raw=result,
    )
