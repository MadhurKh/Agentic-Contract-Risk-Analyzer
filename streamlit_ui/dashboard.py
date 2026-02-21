import os
import sys
from pathlib import Path
import json

import streamlit as st

# --- Bootstrap: ensure repo root is on sys.path BEFORE importing `src` ---
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.model_adapter import analyze_contract  # noqa: E402
from src.logger import save_run  # noqa: E402


st.set_page_config(page_title="Agentic Contract Risk Analyzer", layout="wide")

with st.sidebar:
    st.header("Settings")
    agentic_on = st.toggle("Agentic mode (5-agent)", value=os.getenv("USE_AGENTIC", "0") == "1")
    enforce_citations = st.toggle("Require regulation citations", value=os.getenv("REQUIRE_REG_CITATIONS", "1") == "1")

    if agentic_on:
        os.environ["USE_AGENTIC"] = "1"
    else:
        os.environ.pop("USE_AGENTIC", None)

    os.environ["REQUIRE_REG_CITATIONS"] = "1" if enforce_citations else "0"

    rag_path = REPO_ROOT / "data" / "rag_index" / "reg_index.pkl"
    if rag_path.exists():
        st.success("RAG index found")
        st.caption(str(rag_path))
    else:
        st.warning("RAG index not found yet")
        st.markdown("---")
        st.subheader("RAG Setup")
        st.write("1) Put PDFs in:")
        st.code("data/regulations/eu_ai_act/\ndata/regulations/australia/", language="text")
        st.write("2) Build index:")
        st.code("python scripts/build_reg_index.py", language="bash")
        st.write("3) Refresh and rerun")

st.title("Agentic Contract Risk Analyzer")

col1, col2 = st.columns([2, 1])

with col2:
    title = st.text_input("Document title", value="Uploaded Contract")
    run = st.button("Analyze", type="primary")

with col1:
    uploaded = st.file_uploader("Upload contract (.txt) (PDF parsing can be added later)", type=["txt", "pdf"])
    contract_text = ""
    if uploaded is not None:
        if uploaded.name.lower().endswith(".txt"):
            contract_text = uploaded.read().decode("utf-8", errors="ignore")
        else:
            st.info("PDF ingestion in UI is not enabled yet. Convert PDF to text or paste text below.")
    contract_text = st.text_area("Or paste contract text", value=contract_text, height=320)

# IMPORTANT: ContractMeta.source_type must be "paste" or "upload" per schema
source_type = "upload" if uploaded is not None else "paste"
st.caption(f"Source type: {source_type}")

if run:
    if not contract_text.strip():
        st.error("Please upload or paste contract text.")
    else:
        with st.spinner("Running analysis..."):
            result = analyze_contract(contract_text=contract_text, title=title, source_type=source_type)
            try:
                save_run(result)
            except Exception:
                pass

        st.success("Analysis complete")

        st.markdown("### Summary")
        c1, c2, c3 = st.columns(3)
        c1.metric("Overall Risk Score", getattr(result.summary, "overall_risk_score", "NA"))
        c2.metric("Risk Level", getattr(result.summary, "risk_level", "NA"))
        c3.metric("Findings", len(getattr(result, "findings", []) or []))

        scorecard = None
        for ev in getattr(result, "audit", []) or []:
            if getattr(ev, "event", "") == "AGENTIC_RUN":
                scorecard = (getattr(ev, "details", {}) or {}).get("scorecard")
                break

        if scorecard:
            st.markdown("### Executive Risk Scorecard")
            s1, s2, s3 = st.columns(3)
            s1.metric("Score", scorecard.get("overall_score", "NA"))
            s2.metric("Level", scorecard.get("risk_level", "NA"))
            counts = scorecard.get("counts", {})
            s3.metric("Needs Review", counts.get("needs_review", "NA"))

            with st.expander("Top risks", expanded=True):
                for item in scorecard.get("top_risks", [])[:5]:
                    st.write(f"- [{item.get('severity','')}] {item.get('title','')}")

            with st.expander("Recommended next steps", expanded=False):
                for step in scorecard.get("recommended_next_steps", []):
                    st.write(f"- {step}")

            if scorecard.get("disclaimer"):
                st.caption(scorecard["disclaimer"])

        st.markdown("### Findings")
        for f in getattr(result, "findings", []) or []:
            with st.expander(f"[{f.severity}] {f.finding_id}: {f.risk_statement[:120]}"):
                st.write(f"**Category:** {f.category}")
                st.write(f"**Confidence:** {f.confidence}")
                st.write(f"**Recommendation:** {f.recommendation}")

                if getattr(f, "evidence", None):
                    st.write("**Evidence**")
                    for e in f.evidence[:6]:
                        st.code(f"{e.clause_ref}: {e.snippet}", language="text")

        with st.expander("Raw JSON (debug)", expanded=False):
            st.code(result.model_dump_json(indent=2) if hasattr(result, "model_dump_json") else json.dumps(result.__dict__, indent=2, default=str))
