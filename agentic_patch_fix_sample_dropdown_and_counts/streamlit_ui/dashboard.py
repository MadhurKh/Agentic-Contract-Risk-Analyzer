from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

# --- Robust repo root discovery + imports ------------------------------------
_THIS_FILE = Path(__file__).resolve()

def _find_repo_root(start: Path) -> Path:
    """
    Walk upwards until we find a folder that looks like the repo root.
    Heuristics: contains 'src' package dir and 'streamlit_ui' dir.
    """
    cur = start
    for _ in range(8):
        if (cur / "src").is_dir() and (cur / "streamlit_ui").is_dir():
            return cur
        cur = cur.parent
    # fallback: two levels up from streamlit_ui/
    return _THIS_FILE.parents[1]

REPO_ROOT = _find_repo_root(_THIS_FILE.parent)

# Ensure repo root is importable (so `import src...` works under Streamlit)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.model_adapter import analyze_contract  # noqa: E402


# --- Helpers -----------------------------------------------------------------
def _safe_get(d: Any, *keys: str, default=None):
    cur = d
    for k in keys:
        if cur is None:
            return default
        if isinstance(cur, dict):
            cur = cur.get(k, None)
        else:
            cur = getattr(cur, k, None)
    return default if cur is None else cur

def _as_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return {}

def _discover_sample_contracts() -> Tuple[Path, List[Path]]:
    sample_dir = REPO_ROOT / "sample_data" / "contracts"
    if not sample_dir.exists():
        return sample_dir, []
    files = sorted([p for p in sample_dir.glob("*.txt") if p.is_file()])
    return sample_dir, files

def _read_text_file(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="utf-8", errors="ignore")

def _severity_rank(sev: str) -> int:
    s = (sev or "").strip().lower()
    if s == "critical":
        return 4
    if s == "high":
        return 3
    if s == "medium":
        return 2
    if s == "low":
        return 1
    return 0

def _compute_avg_severity(findings: List[Dict[str, Any]]) -> float:
    if not findings:
        return 0.0
    vals = [_severity_rank(f.get("severity", "")) for f in findings]
    vals = [v for v in vals if v > 0]
    return round(sum(vals) / max(len(vals), 1), 2)

def _count_review_status(findings: List[Dict[str, Any]]) -> Tuple[int, int]:
    verified = 0
    needs_review = 0
    for f in findings:
        status = (f.get("status") or "").upper()
        if status == "VERIFIED":
            verified += 1
        elif status == "NEEDS_REVIEW":
            needs_review += 1
        else:
            # fallback: treat missing/unknown as needs_review when citations required
            if f.get("needs_review") is True:
                needs_review += 1
    return verified, needs_review

def _format_finding_header(f: Dict[str, Any]) -> str:
    sev = (f.get("severity") or "Low").title()
    code = f.get("code") or ""
    title = f.get("title") or f.get("category") or ""
    parts = [f"[{sev}]"]
    if code:
        parts.append(code)
    if title:
        parts.append(title)
    return " ".join(parts).strip()

def _truncate(s: str, n: int = 110) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    return s[: n - 1].rstrip() + "…"


# --- Page --------------------------------------------------------------------
st.set_page_config(page_title="Agentic Contract Risk Analyzer", layout="wide")

st.title("Agentic Contract Risk Analyzer")
st.caption("MVP agentic pipeline (Extractor → Obligation Mapper → Auditor → Verifier → Reviewer) with explainable scoring + evidence.")

# Sidebar settings
with st.sidebar:
    st.header("Settings")
    agentic_mode = st.toggle("Agentic mode (5-agent)", value=True)
    require_citations = st.toggle("Require regulation citations", value=True)

    st.divider()
    st.header("Sample contracts")
    sample_dir, sample_files = _discover_sample_contracts()
    if not sample_files:
        st.info(f"No samples found under {sample_dir.as_posix()}")
        selected_sample = None
    else:
        labels = [p.name for p in sample_files]
        selected_label = st.selectbox("Load a sample (optional)", labels, index=0)
        selected_sample = sample_files[labels.index(selected_label)]

    st.divider()
    # RAG index status (optional)
    rag_index_path = REPO_ROOT / "data" / "rag_index" / "reg_index.pkl"
    if rag_index_path.exists():
        st.success("RAG index found")
        st.caption(str(rag_index_path))
    else:
        st.warning("RAG index not found")
        st.caption(str(rag_index_path))

# Input area
col_left, col_right = st.columns([2, 1], gap="large")

with col_left:
    uploaded = st.file_uploader("Upload contract (.txt)", type=["txt"])
    st.write("Or paste contract text")
    contract_text = st.text_area("Contract text", height=280, label_visibility="visible")

with col_right:
    title = st.text_input("Document title", value="Uploaded Contract")
    source_type = st.selectbox("Source type", options=["paste", "upload"], index=0)
    analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)

# Load sample if chosen and no user input yet
if selected_sample and not uploaded and not contract_text.strip():
    contract_text = _read_text_file(selected_sample)
    st.session_state["Contract text"] = contract_text  # keep UI synced
    title = selected_sample.stem.replace("_", " ").title()
    source_type = "paste"

# If file uploaded, use it
if uploaded is not None:
    try:
        content = uploaded.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        content = uploaded.getvalue().decode("utf-8", errors="ignore")
    contract_text = content
    source_type = "upload"

if analyze_clicked:
    if not contract_text.strip():
        st.error("Please provide contract text (paste or upload a .txt file).")
        st.stop()

    with st.spinner("Analyzing contract..."):
        result_model = analyze_contract(
            contract_text,
            title=title,
            source_type=source_type,
            agentic_mode=agentic_mode,
            require_reg_citations=require_citations,
        )

    result = _as_dict(result_model)

    findings: List[Dict[str, Any]] = result.get("findings", []) or []
    score_overall = _safe_get(result, "summary", "overall_risk_score", default=None)
    risk_level = _safe_get(result, "summary", "risk_level", default=None)

    # Prefer reviewer scorecard if present
    scorecard = result.get("scorecard", {}) or result.get("executive_scorecard", {}) or {}
    scorecard_score = scorecard.get("score")
    scorecard_level = scorecard.get("risk_level")

    # Fallbacks
    if score_overall is None:
        score_overall = _safe_get(result, "scoring", "normalized_score_0_100", default=0)
    if risk_level is None:
        risk_level = _safe_get(result, "scoring", "risk_level", default="Low")

    # Normalize types
    try:
        score_overall_int = int(round(float(score_overall)))
    except Exception:
        score_overall_int = 0

    # Header KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Overall Risk Score", f"{score_overall_int}")
    k2.metric("Risk Level", str(risk_level))
    k3.metric("Findings", f"{len(findings)}")

    st.divider()

    # Executive scorecard
    st.subheader("Executive Scorecard")
    c1, c2, c3 = st.columns(3)
    # Make sure the number matches the KPI
    sc_score = scorecard_score if scorecard_score is not None else score_overall_int
    try:
        sc_score_f = float(sc_score)
    except Exception:
        sc_score_f = float(score_overall_int)

    c1.metric("Scorecard score", f"{sc_score_f:.1f}")
    c2.metric("Scorecard risk level", str(scorecard_level or risk_level))

    verified, needs_review = _count_review_status(findings)
    # IMPORTANT: show as Verified / Needs review (not reversed)
    c3.metric("Verified / Needs review", f"{verified} / {needs_review}")

    # Summary text (build deterministically from current output)
    avg_sev = _compute_avg_severity(findings)
    top3 = sorted(findings, key=lambda f: _severity_rank(f.get("severity", "")), reverse=True)[:3]
    top_names = [_truncate((f.get("title") or f.get("recommendation") or f.get("code") or "Risk"), 70) for f in top3]
    needs_review_note = ""
    if needs_review > 0:
        needs_review_note = f" {needs_review} items require additional grounding/citations before conclusions can be finalized."

    st.info(
        f"Risk level is **{str(scorecard_level or risk_level).upper()}** "
        f"(score {sc_score_f:.1f}/100; avg severity {avg_sev}/4).{needs_review_note} "
        f"Top exposure areas include: {', '.join(top_names) if top_names else 'N/A'}."
    )

    # Top risks list
    st.markdown("### Top risks")
    if not top3:
        st.write("No high-signal risks detected.")
    else:
        for f in top3:
            sev = (f.get("severity") or "Low").upper()
            title_line = _truncate((f.get("title") or f.get("category") or "Risk"), 110)
            rec = _truncate((f.get("recommendation") or ""), 90)
            st.write(f"• **{sev}** — {title_line}{(' — ' + rec) if rec else ''}")

    # Recommended next steps
    st.markdown("### Recommended next steps")
    steps: List[str] = []
    if require_citations and needs_review > 0:
        steps.append(f"Resolve **NEEDS_REVIEW** items by adding missing regulatory citations and explicit contractual commitments. (Missing regulation citations: {needs_review})")
    steps.append("Confirm applicability scope (high-risk vs limited-risk) and align contractual commitments.")
    steps.append("Add measurable controls: logging retention, audit rights, oversight escalation, incident SLAs.")
    for s in steps:
        st.write(f"• {s}")

    st.divider()

    # Findings detail
    st.header("Findings")
    if not findings:
        st.write("No findings.")
    else:
        for f in findings:
            header = _format_finding_header(f)
            with st.expander(header, expanded=False):
                st.write(f"**Category:** {f.get('category','General')}")
                st.write(f"**Status:** {f.get('status','')}")
                conf = f.get("confidence")
                if conf is not None:
                    st.write(f"**Confidence:** {conf}")
                if f.get("recommendation"):
                    st.write("**Recommendation:**")
                    st.write(f.get("recommendation"))
                if f.get("evidence"):
                    st.write("**Evidence:**")
                    st.code(f.get("evidence"), language="text")
                cits = f.get("reg_citations") or f.get("citations") or []
                if cits:
                    st.write("**Regulatory citations:**")
                    for c in cits[:5]:
                        if isinstance(c, dict):
                            st.write(f"- {c.get('title') or c.get('ref') or c}")
                        else:
                            st.write(f"- {c}")

    # Debug
    with st.expander("Raw JSON (debug)"):
        st.json(result)
