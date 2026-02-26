import os
import sys
from pathlib import Path
import streamlit as st

# Ensure project root is on sys.path so `import src.*` works even when running from `streamlit_ui/`
_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.model_adapter import analyze_contract
from src.ui_view_model import build_ui_view

st.set_page_config(
    page_title="Agentic Contract Risk Analyzer",
    page_icon="🧠",
    layout="wide",
)

# -----------------------------
# Sidebar: Inputs (FROZEN UI)
# -----------------------------
st.sidebar.markdown("## Inputs")

input_mode = st.sidebar.radio(
    "Input mode",
    ["Sample contract", "Paste text", "Upload file"],
    index=0,
)

contract_title = st.sidebar.text_input("Contract title", value="Uploaded Contract")

sample_choice = None
contract_text = ""

if input_mode == "Sample contract":
    # Default sample directory (repo-relative)
    sample_dir = _PROJECT_ROOT / "sample_data"
    samples = []
    if sample_dir.exists():
        samples = sorted([p.name for p in sample_dir.glob("*.txt")])
    if not samples:
        samples = ["sample_contract_large.txt"]
    sample_choice = st.sidebar.selectbox("Choose a sample contract", samples, index=0)
    sample_path = sample_dir / sample_choice
    if sample_path.exists():
        contract_text = sample_path.read_text(encoding="utf-8", errors="ignore")
        st.sidebar.caption(f"Loaded: {sample_path.as_posix()}")
    else:
        contract_text = ""
        st.sidebar.caption("Loaded: (sample file not found in sample_data/)")

elif input_mode == "Paste text":
    contract_text = st.sidebar.text_area("Paste contract text", height=260)
else:
    uploaded = st.sidebar.file_uploader("Upload contract file (.txt)", type=["txt"])
    if uploaded is not None:
        contract_text = uploaded.read().decode("utf-8", errors="ignore")
        st.sidebar.caption(f"Loaded: {uploaded.name}")

st.sidebar.markdown("---")
st.sidebar.markdown("## Run mode")

agentic_mode = st.sidebar.toggle("Agentic mode", value=True)
require_reg_citations = st.sidebar.toggle("Require regulation citations (local PDFs)", value=True)

jurisdictions = st.sidebar.multiselect("Jurisdictions", ["EU", "AU"], default=["EU", "AU"])

analyze_clicked = st.sidebar.button("Analyze", type="primary", use_container_width=True)

# -----------------------------
# Main: Results
# -----------------------------
st.title("Agentic Contract Risk Analyzer")

if analyze_clicked:
    with st.spinner("Analyzing contract..."):
        result = analyze_contract(
            contract_text=contract_text or "",
            title=contract_title or "Uploaded Contract",
            # NOTE: Sample contract is a text source internally.
            source_type=("paste" if input_mode == "Sample contract" else ("paste" if input_mode == "Paste text" else "upload")),
            agentic_mode=agentic_mode,
            require_reg_citations=require_reg_citations,
            jurisdictions=jurisdictions,
        )
        ui = build_ui_view(result)

    st.divider()

    left, right = st.columns([2, 1])

    # Left: Executive Summary (bullets) + Top Risks
    with left:
        st.header("Executive Summary")

        # Keep exact bullet formatting (do not change UI layout)
        for line in ui.exec_summary_lines:
            st.markdown(f"- {line}")

        st.subheader("Top Risks")
        for r in ui.top_risks:
            sev = r.get("severity", "Unknown")
            title = r.get("title", "")
            if title:
                st.markdown(f"- **{sev}** — {title}")

    # Right: Score panel (frozen)
    with right:
        st.header("Score")
        st.caption("Risk level")
        st.markdown(f"## {ui.risk_level.upper()}")
        st.caption("Score (0–100)")
        st.markdown(f"## {ui.score_0_100}")
        st.caption("Needs review")
        st.markdown(f"## {ui.needs_review}")
        st.caption("Verified")
        st.markdown(f"## {ui.verified}")

    st.divider()

    # Findings
    st.header("Findings")
    for f in ui.findings:
        sev = getattr(f, "severity", "Unknown")
        status = getattr(f, "status", "") or ""
        cat = getattr(f, "category", "General")
        stmt = getattr(f, "risk_statement", "") or ""
        conf = getattr(f, "confidence", None)
        qreasons = getattr(f, "quality_reason_codes", None) or []
        reg_cits = getattr(f, "reg_citations", None) or []
        evid = getattr(f, "evidence", None) or []
        rec = getattr(f, "recommendation", None)

        header_stmt = stmt[:120] + ("..." if len(stmt) > 120 else "")
        with st.expander(f"[{sev}] {cat}: {header_stmt}"):
            # Status line (helps explain remaining NEEDS_REVIEW items; no layout changes)
            cols = st.columns([1, 1, 1])
            with cols[0]:
                st.markdown(f"**Status:** {status or '—'}")
            with cols[1]:
                if conf is not None:
                    try:
                        st.markdown(f"**Confidence:** {float(conf):.2f}")
                    except Exception:
                        st.markdown(f"**Confidence:** {conf}")
                else:
                    st.markdown("**Confidence:** —")
            with cols[2]:
                st.markdown(f"**Reg citations:** {len(reg_cits)}")

            st.write(stmt)

            if qreasons:
                st.markdown("**Needs review because:**")
                for r in qreasons:
                    st.markdown(f"- {r}")

            if rec:
                st.markdown("**Recommendation**")
                st.write(rec)

            if evid:
                st.markdown("**Evidence**")
                # Show clause_ref + snippet (clause_ref will show doc_id for regulation evidence)
                for e in evid:
                    try:
                        clause_ref = getattr(e, "clause_ref", "") or ""
                        snippet = getattr(e, "snippet", "") or ""
                    except Exception:
                        clause_ref = ""
                        snippet = ""
                    if clause_ref:
                        st.markdown(f"**{clause_ref}**")
                    if snippet:
                        st.code(snippet, language="text")

    # Raw JSON (Option A)
    with st.expander("Raw JSON (debug/export)", expanded=False):
        raw_obj = getattr(ui, "raw", None)
        if raw_obj is not None and hasattr(raw_obj, "model_dump"):
            st.json(raw_obj.model_dump())
        elif raw_obj is not None and hasattr(raw_obj, "dict"):
            st.json(raw_obj.dict())
        elif raw_obj is not None and hasattr(raw_obj, "__dict__"):
            st.json(raw_obj.__dict__)
        else:
            st.json(raw_obj if raw_obj is not None else {})
else:
    st.info("Choose input options on the left, then click **Analyze**.")
