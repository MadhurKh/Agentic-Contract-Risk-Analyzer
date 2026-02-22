"""Streamlit dashboard for Agentic Contract Risk Analyzer.

This file is intentionally defensive about schema changes.
It:
- locates sample contracts from either sample_data/contracts or sample_data
- calls analyze_contract() with explicit keyword args
- renders findings even if field names differ (title/message/summary etc.)
- computes Verified / Needs review counts robustly
- generates executive summary using the same score shown in the KPI tiles

Drop-in replacement for streamlit_ui/dashboard.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

# --- Import adapter (supports running from repo root OR from streamlit_ui folder) ---
try:
    from src.model_adapter import analyze_contract  # type: ignore
except Exception:
    # fallback: add repo root to path
    import sys

    REPO_ROOT = Path(__file__).resolve().parents[1]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from src.model_adapter import analyze_contract  # type: ignore


# ----------------------------
# Helpers
# ----------------------------

def _safe_get(d: Any, path: List[str], default: Any = None) -> Any:
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
    return cur if cur is not None else default


def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _coerce_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _coerce_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return default
        return int(float(x))
    except Exception:
        return default


def _truncate(s: str, n: int = 120) -> str:
    s = s or ""
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def _pick_text(f: Dict[str, Any]) -> str:
    """Choose best display text for a finding across evolving schemas."""
    # Most specific first
    for key in [
        "display",
        "title",
        "name",
        "finding_title",
        "risk_statement",
        "obligation_title",
        "obligation_name",
        "summary",
        "message",
        "description",
        "details",
        "recommendation",
    ]:
        v = f.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()

    # Common nested containers
    for nested in ["finding", "risk", "obligation", "meta"]:
        v = f.get(nested)
        if isinstance(v, dict):
            for key in ["title", "name", "summary", "message", "description"]:
                vv = v.get(key)
                if isinstance(vv, str) and vv.strip():
                    return vv.strip()

    # Fallback: show id/category
    fid = f.get("id") or f.get("finding_id") or f.get("code")
    cat = f.get("category") or f.get("risk_category")
    parts = [p for p in [str(fid) if fid else "", str(cat) if cat else ""] if p]
    return " — ".join(parts) if parts else "(finding)"


def _pick_severity(f: Dict[str, Any]) -> str:
    sev = f.get("severity") or f.get("risk_level") or f.get("level")
    if isinstance(sev, str) and sev.strip():
        return sev.strip().capitalize()
    # Sometimes numeric
    sev_n = f.get("severity_score") or f.get("severity_num")
    if sev_n is not None:
        try:
            v = float(sev_n)
            if v >= 3.5:
                return "High"
            if v >= 2.5:
                return "Medium"
            return "Low"
        except Exception:
            pass
    return ""


def _is_needs_review(f: Dict[str, Any]) -> bool:
    # explicit verdict
    verdict = f.get("verdict") or _safe_get(f, ["verification", "verdict"]) or _safe_get(f, ["verification", "status"])
    if isinstance(verdict, str):
        v = verdict.upper()
        if "NEEDS" in v or "REVIEW" in v:
            return True
        if v == "VERIFIED":
            return False

    # explicit boolean
    for key in ["needs_review", "requires_review", "human_review_required"]:
        if key in f and isinstance(f[key], bool):
            return bool(f[key])

    # missing evidence / citations flags
    if f.get("missing_contract_evidence") or f.get("missing_reg_citations"):
        return True

    # common quality flags
    q = f.get("quality_flags")
    if isinstance(q, list) and q:
        return True

    reasons = f.get("reasons") or _safe_get(f, ["verification", "reasons"])
    if isinstance(reasons, list) and any(isinstance(r, str) and r.strip() for r in reasons):
        # treat any reason as needs review
        return True

    return False


def _verified_needs_review_counts(findings: List[Dict[str, Any]]) -> Tuple[int, int]:
    needs = sum(1 for f in findings if _is_needs_review(f))
    verified = max(0, len(findings) - needs)
    return verified, needs


def _top_risks(findings: List[Dict[str, Any]], k: int = 5) -> List[Tuple[str, str]]:
    """Return list of (severity, text)"""
    items: List[Tuple[float, str, str]] = []
    for f in findings:
        sev_label = _pick_severity(f) or "Medium"
        sev_weight = {"Critical": 4.0, "High": 3.0, "Medium": 2.0, "Low": 1.0}.get(sev_label.capitalize(), 2.0)
        txt = _pick_text(f)
        if txt:
            items.append((sev_weight, sev_label.capitalize(), txt))

    items.sort(key=lambda t: (-t[0], t[2]))
    out: List[Tuple[str, str]] = []
    for _, sev, txt in items[:k]:
        out.append((sev, txt))
    return out


def _load_samples() -> Dict[str, str]:
    """Return mapping: display_name -> text."""
    root = Path(__file__).resolve().parents[1]
    # Accept either structure:
    #   sample_data/contracts/*.txt
    #   sample_data/*.txt
    base = root / "sample_data"
    candidates: List[Path] = []

    if (base / "contracts").exists():
        candidates.extend(sorted((base / "contracts").glob("*.txt")))
        candidates.extend(sorted((base / "contracts").glob("*.md")))

    if base.exists():
        candidates.extend(sorted(base.glob("*.txt")))
        candidates.extend(sorted(base.glob("*.md")))

    # de-dupe
    seen = set()
    uniq: List[Path] = []
    for p in candidates:
        if p.resolve() in seen:
            continue
        seen.add(p.resolve())
        uniq.append(p)

    samples: Dict[str, str] = {}
    for p in uniq:
        try:
            samples[p.name] = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

    return samples


# ----------------------------
# UI
# ----------------------------

st.set_page_config(page_title="Agentic Contract Risk Analyzer", layout="wide")

st.sidebar.title("Settings")
agentic_mode = st.sidebar.toggle("Agentic mode (5-agent)", value=True)
require_citations = st.sidebar.toggle("Require regulation citations", value=True)

st.title("Agentic Contract Risk Analyzer")
st.caption("MVP agentic pipeline (Extractor → Obligation Mapper → Auditor → Verifier → Reviewer) with explainable scoring + evidence.")

# Samples
st.sidebar.subheader("Sample contracts")
samples = _load_samples()
if samples:
    sample_name = st.sidebar.selectbox("Load a sample (optional)", options=["(none)"] + list(samples.keys()))
else:
    st.sidebar.info("No samples found under sample_data (or sample_data/contracts)")
    sample_name = "(none)"

# RAG index indicator (best effort)
rag_index_path = Path(__file__).resolve().parents[1] / "data" / "rag_index" / "reg_index.pkl"
if rag_index_path.exists():
    st.sidebar.success("RAG index found")
    st.sidebar.caption(str(rag_index_path))
else:
    st.sidebar.warning("RAG index not found")
    st.sidebar.caption(str(rag_index_path))

# Inputs
col1, col2 = st.columns([2, 1])
with col1:
    uploaded = st.file_uploader("Upload contract (.txt)", type=["txt"])
    st.write("Or paste contract text")
    contract_text = st.text_area("Contract text", height=280)

with col2:
    title = st.text_input("Document title", value="Uploaded Contract")
    source_type = st.selectbox("Source type", options=["paste", "upload"], index=0)
    run_btn = st.button("Analyze", type="primary")

# If a sample is selected, populate contract_text
if sample_name and sample_name != "(none)":
    contract_text = samples.get(sample_name, contract_text)
    title = sample_name

# If file uploaded, override
if uploaded is not None:
    try:
        file_text = uploaded.getvalue().decode("utf-8", errors="ignore")
        contract_text = file_text
        source_type = "upload"
        if title == "Uploaded Contract":
            title = uploaded.name
    except Exception:
        pass

if run_btn:
    if not (contract_text or "").strip():
        st.error("Please upload a file or paste contract text.")
        st.stop()

    with st.spinner("Analyzing contract…"):
        result_obj = analyze_contract(
            contract_text=contract_text,
            title=title,
            source_type=source_type,
            agentic_mode=agentic_mode,
            require_reg_citations=require_citations,
        )

    # Convert pydantic model to dict if needed
    result: Dict[str, Any]
    if hasattr(result_obj, "model_dump"):
        result = result_obj.model_dump()  # type: ignore
    elif isinstance(result_obj, dict):
        result = result_obj
    else:
        result = json.loads(json.dumps(result_obj, default=str))

    findings = _as_list(result.get("findings"))
    findings = [f for f in findings if isinstance(f, dict)]

    # Score / risk level: prefer top KPI value, then scorecard
    overall_score = (
        _coerce_float(_safe_get(result, ["summary", "overall_risk_score"], None), None)
        if _safe_get(result, ["summary", "overall_risk_score"], None) is not None
        else None
    )
    if overall_score is None:
        overall_score = _coerce_float(_safe_get(result, ["scorecard", "score"], None), 0.0)
    if overall_score == 0.0:
        overall_score = _coerce_float(_safe_get(result, ["scoring", "normalized_score_0_100"], None), overall_score)
    overall_score_int = _coerce_int(round(overall_score), 0)

    risk_level = (
        _safe_get(result, ["summary", "risk_level"], None)
        or _safe_get(result, ["scorecard", "risk_level"], None)
        or _safe_get(result, ["scoring", "risk_level"], None)
        or "Unknown"
    )

    # KPI row
    k1, k2, k3 = st.columns(3)
    k1.metric("Overall Risk Score", value=str(overall_score_int))
    k2.metric("Risk Level", value=str(risk_level).capitalize())
    k3.metric("Findings", value=str(len(findings)))

    # Executive scorecard (kept aligned to KPIs)
    st.subheader("Executive Scorecard")
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Scorecard score", value=f"{overall_score:.1f}")
    sc2.metric("Scorecard risk level", value=str(risk_level).capitalize())

    verified_cnt, needs_cnt = _verified_needs_review_counts(findings)
    sc3.metric("Verified / Needs review", value=f"{verified_cnt} / {needs_cnt}")

    avg_sev = None
    if findings:
        sev_map = {"Critical": 4.0, "High": 3.0, "Medium": 2.0, "Low": 1.0}
        vals = []
        for f in findings:
            s = _pick_severity(f)
            if s in sev_map:
                vals.append(sev_map[s])
        if vals:
            avg_sev = sum(vals) / len(vals)

    top = _top_risks(findings, k=3)
    top_text = "; ".join([_truncate(t, 140) for _, t in top]) if top else "(no findings)"

    summary_bits = [
        f"Risk level is **{str(risk_level).upper()}** (score **{overall_score:.1f}/100**" + (f"; avg severity **{avg_sev:.2f}/4**" if avg_sev is not None else "") + ").",
    ]

    if needs_cnt > 0:
        summary_bits.append(f"**{needs_cnt}** item(s) require additional grounding/citations before conclusions can be finalized.")

    if top_text and top_text != "(no findings)":
        summary_bits.append(f"Top exposure areas include: {top_text}.")

    st.info(" ".join(summary_bits))

    # Top risks
    st.subheader("Top risks")
    if top:
        for sev, txt in top:
            st.markdown(f"- **{sev.upper()}** — {_truncate(txt, 220)}")
    else:
        st.write("No risks identified.")

    # Recommended next steps (prefer from result, else derived)
    st.subheader("Recommended next steps")
    recs = _as_list(_safe_get(result, ["recommendations"], None) or _safe_get(result, ["summary", "recommended_next_steps"], None))
    recs = [r for r in recs if isinstance(r, str) and r.strip()]
    if not recs:
        recs = [
            "Confirm applicability scope (high-risk vs limited-risk) and align contractual commitments.",
            "Add measurable controls: logging retention, audit rights, oversight escalation, incident SLAs.",
        ]
        if needs_cnt > 0:
            recs.insert(0, "Resolve NEEDS_REVIEW items by adding missing evidence/citations and explicit contractual commitments.")
    for r in recs:
        st.markdown(f"- {r}")

    # Findings
    st.subheader("Findings")
    if not findings:
        st.write("No findings.")
    else:
        for f in findings:
            sev = _pick_severity(f)
            cat = f.get("category") or f.get("risk_category") or ""
            head = " ".join([p for p in [f"[{sev}]" if sev else "", str(cat)] if p]).strip() or "Finding"
            body = _pick_text(f)

            with st.expander(f"{head}: {_truncate(body, 160)}", expanded=False):
                st.write(body)

                # Evidence / citations
                ev = f.get("evidence") or f.get("contract_evidence") or _safe_get(f, ["verification", "evidence"], None)
                cites = f.get("reg_citations") or f.get("citations") or _safe_get(f, ["verification", "reg_citations"], None)

                if ev:
                    st.markdown("**Contract evidence**")
                    if isinstance(ev, list):
                        for e in ev:
                            st.write(e)
                    else:
                        st.write(ev)

                if cites:
                    st.markdown("**Regulation citations**")
                    if isinstance(cites, list):
                        for c in cites:
                            st.write(c)
                    else:
                        st.write(cites)

                verdict = f.get("verdict") or _safe_get(f, ["verification", "verdict"]) or _safe_get(f, ["verification", "status"])
                if verdict:
                    st.markdown(f"**Verification:** {verdict}")

                reasons = f.get("reasons") or _safe_get(f, ["verification", "reasons"])
                if reasons:
                    st.markdown("**Reasons:**")
                    for r in _as_list(reasons):
                        st.write(r)

    with st.expander("Raw JSON (debug)"):
        st.json(result)
