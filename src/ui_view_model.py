from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .schemas import AnalysisResult, Finding
from .ui_text import safe_truncate


@dataclass
class UIView:
    score_0_100: int
    risk_level: str
    verified_count: int
    needs_review_count: int
    exec_summary_lines: List[str]
    key_themes: List[str]
    top_risks: List[Dict[str, Any]]
    findings: List[Finding]
    raw: AnalysisResult

    @property
    def verified(self) -> int:
        return int(getattr(self, "verified_count", 0) or 0)

    @property
    def needs_review(self) -> int:
        return int(getattr(self, "needs_review_count", 0) or 0)

    @property
    def exec_summary(self) -> str:
        lines = getattr(self, "exec_summary_lines", None) or []
        return "\n".join([str(x) for x in lines if str(x).strip()])


_PREFIX_PATTERNS = [
    r"^potential\s+gap\s+vs\s+obligation\s*[:\-\s]*",
    r"^gap\s+vs\s+obligation\s*[:\-\s]*",
]

# Common truncation repairs (observed in your UI output)
_COMPLETION_MAP = {
    "data governance and data qualit": "Data governance and data quality",
    "accuracy, robustness, cybersecu": "Accuracy, robustness, cybersecurity",
    "cybersecu": "cybersecurity",
    "qualit": "quality",
}


def _safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(round(float(x)))
    except Exception:
        return default


def _safe_str(x: Any, default: str = "") -> str:
    return default if x is None else str(x)


def _apply_completion_map(t: str) -> str:
    low = t.lower().strip()
    if low in _COMPLETION_MAP:
        return _COMPLETION_MAP[low]
    # Repair truncated tail tokens
    for bad, good in _COMPLETION_MAP.items():
        if low.endswith(bad):
            # Replace only at end (case-insensitive)
            return re.sub(re.escape(bad) + r"$", good, t, flags=re.IGNORECASE)
    return t


def _strip_prefix(t: str) -> str:
    out = t
    for pat in _PREFIX_PATTERNS:
        out = re.sub(pat, "", out, flags=re.IGNORECASE).strip()
    return out


def _clean_obligation_title(raw: str) -> str:
    # Create a short title-like string for themes (no repetitive prefix).
    t = (raw or "").strip()
    if not t:
        return ""
    t = _strip_prefix(t)

    # If it contains quoted obligation, prefer that
    m = re.search(r"'([^']+)'", t)
    if m:
        t = m.group(1).strip()

    t = t.strip(" \"'")
    t = t.rstrip(" ,;:-")
    t = _apply_completion_map(t)
    return t


def _theme_from_finding(f: Finding) -> str:
    # Theme based on obligation title (short), not the full finding sentence.
    base = _clean_obligation_title(getattr(f, "risk_statement", "") or "")
    if not base:
        base = _clean_obligation_title(getattr(f, "category", "") or "Risk")
    # Keep themes tidy; word-safe truncation only if extremely long.
    return safe_truncate(base, 140)


def _infer_counts(findings: List[Finding]) -> Tuple[int, int]:
    """Canonical status-based counts (single source of truth).

    Verified      => status == 'VERIFIED'
    Needs review  => status == 'NEEDS_REVIEW'
    Other/None    => ignored for counts (treated as Draft/Other)
    """
    verified = 0
    needs_review = 0
    for f in findings:
        st = (getattr(f, "status", None) or "").upper().strip()
        if st == "VERIFIED":
            verified += 1
        elif st == "NEEDS_REVIEW":
            needs_review += 1
    return verified, needs_review



def build_ui_view(result: AnalysisResult) -> UIView:
    score = result.scoring.normalized_score_0_100 if result.scoring else result.summary.overall_risk_score
    risk_level = result.scoring.risk_level if result.scoring else result.summary.risk_level

    findings = result.findings or []
    verified, needs_review = _infer_counts(findings)

    # ---------- Top Risks (FULL SENTENCES; no truncation) ----------
    # Locked behavior (P2 / Option 2): Top N findings by severity (then confidence),
    # allowing Medium if there are not enough High/Critical items.
    top_risks: List[Dict[str, Any]] = []

    _sev_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

    def _risk_rank(f: Finding) -> Tuple[int, float]:
        sev = str(getattr(f, "severity", "Medium")).upper().strip()
        conf = float(getattr(f, "confidence", 0.0) or 0.0)
        return (_sev_rank.get(sev, 2), conf)

    ranked = sorted(
        [f for f in findings if (getattr(f, "risk_statement", "") or "").strip()],
        key=_risk_rank,
        reverse=True,
    )

    def _top_risk_key(f: Finding) -> str:
        fid = str(getattr(f, "finding_id", "") or "").strip()
        m = re.match(r"^F-\d+-(.+)$", fid)
        if m:
            return m.group(1).strip()
        if fid:
            return fid
        # Fallback to stable composite key
        cat = str(getattr(f, "category", "") or "").strip()
        rs = str(getattr(f, "risk_statement", "") or "").strip()
        return f"{cat}|{rs}"

    seen_keys = set()
    for f in ranked:
        if len(top_risks) >= 5:
            break
        k = _top_risk_key(f).lower()
        if k in seen_keys:
            continue
        seen_keys.add(k)

        rs = (getattr(f, "risk_statement", "") or "").strip()
        rs = _apply_completion_map(rs)
        top_risks.append(
            {
                "severity": getattr(f, "severity", None),
                "category": getattr(f, "category", "Risk"),
                # Full sentence for display (Streamlit will wrap)
                "title": rs,
            }
        )

    # ---------- Themes (SMART SUMMARY; non-repetitive) ----------
    themes: List[str] = []
    seen = set()
    for f in findings[:25]:
        th = _theme_from_finding(f)
        key = th.lower()
        if th and key not in seen:
            seen.add(key)
            themes.append(th)
        if len(themes) >= 3:
            break

    exec_lines = [
        f"Risk level: **{str(risk_level).upper()}**  |  Score: **{float(score):.1f}/100**",
        f"Quality check: **{needs_review}** items need review/grounding  |  **{verified}** verified",
        "Key exposure themes: " + (", ".join(themes) if themes else "No dominant themes detected."),
        "Next action: Validate clauses against policy/regulation sources and remediate missing obligations.",
    ]

    return UIView(
        score_0_100=_safe_int(score),
        risk_level=_safe_str(risk_level),
        verified_count=verified,
        needs_review_count=needs_review,
        exec_summary_lines=exec_lines,
        key_themes=themes,
        top_risks=top_risks,
        findings=findings,
        raw=result,
    )
