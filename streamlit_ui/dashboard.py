from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

import streamlit as st

# --- Make repo root importable (so `import src.*` works when running from streamlit_ui/) ---
_THIS = Path(__file__).resolve()
_REPO_ROOT = _THIS.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.model_adapter import analyze_contract
from src.schemas import AnalysisResult
from src.ui_view_model import build_ui_view
from src.ui_text import safe_truncate


st.set_page_config(page_title="Agentic Contract Risk Analyzer", layout="wide")


def _find_sample_files(repo_root: Path) -> List[Path]:
    c1 = repo_root / "sample_data"
    c2 = repo_root / "sample_data" / "contracts"
    paths = []
    for base in (c1, c2):
        if base.exists() and base.is_dir():
            paths.extend(sorted(base.glob("*.txt")))
    # de-dupe
    seen = set()
    out = []
    for p in paths:
        if p.resolve() in seen:
            continue
        seen.add(p.resolve())
        out.append(p)
    return out


def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return p.read_text(errors="ignore")


st.title("Agentic Contract Risk Analyzer")

with st.sidebar:
    st.header("Input")
    mode = st.radio("Source", ["Paste", "Upload", "Sample"], horizontal=False)

    title = st.text_input("Contract title", value="Uploaded Contract")

    contract_text = ""
    if mode == "Paste":
        contract_text = st.text_area("Paste contract text", height=260)
        source_type = "paste"
    elif mode == "Upload":
        up = st.file_uploader("Upload .txt contract", type=["txt"])
        source_type = "upload"
        if up is not None:
            contract_text = up.read().decode("utf-8", errors="ignore")
            if not title or title == "Uploaded Contract":
                title = up.name
    else:
        source_type = "paste"
        samples = _find_sample_files(_REPO_ROOT)
        if samples:
            labels = [p.name for p in samples]
            choice = st.selectbox("Choose a sample contract", labels, index=0)
            p = samples[labels.index(choice)]
            contract_text = _read_text(p)
        else:
            st.info("No sample contracts found. Put .txt files in sample_data/ or sample_data/contracts/.")

    st.divider()
    st.header("Run mode")
    agentic_mode = st.toggle("Agentic mode", value=True)
    require_citations = st.toggle("Require regulation citations", value=True)
    jurisdictions = st.multiselect("Jurisdictions", options=["EU", "AU"], default=["EU", "AU"])

    analyze = st.button("Analyze", type="primary")


if analyze:
    if not contract_text.strip():
        st.warning("Please provide contract text (paste, upload, or select a sample).")
        st.stop()

    with st.spinner("Analyzing..."):
        res = analyze_contract(
            contract_text=contract_text,
            title=title,
            source_type=source_type,
            agentic_mode=agentic_mode,
            require_reg_citations=require_citations,
            jurisdictions=jurisdictions,
        )

    # Ensure pydantic object
    if isinstance(res, dict):
        result = AnalysisResult(**res)
    else:
        result = res

    ui = build_ui_view(result)

    # --- KPI row ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall Risk Score", f"{ui.score_0_100}")
    c2.metric("Risk Level", ui.risk_level)
    c3.metric("Verified / Needs review", f"{ui.verified_count} / {ui.needs_review_count}")
    c4.metric("Findings", f"{len(ui.findings)}")

    st.divider()

    # --- Executive scorecard ---
    st.subheader("Executive Scorecard")
    st.info(ui.exec_summary)

    st.markdown("**Top Risks**")
    for t in ui.top_risks[:5]:
        sev = t.get("severity") or ""
        sev_txt = f"**{sev}** — " if sev else ""
        st.write(f"- {sev_txt}{safe_truncate(t.get('title',''), 110)}")

    st.divider()

    # --- Findings ---
    st.subheader("Findings")
    if not ui.findings:
        st.success("No findings detected for the given contract.")
    else:
        for f in ui.findings:
            header = f"[{f.severity}] {f.category}: {safe_truncate(f.risk_statement, 120)}"
            with st.expander(header, expanded=False):
                st.markdown(f"**Risk statement:** {f.risk_statement}")
                st.markdown(f"**Recommendation:** {f.recommendation}")

                st.markdown("**Evidence**")
                if f.evidence:
                    for e in f.evidence[:8]:
                        st.markdown(f"- **{e.clause_ref}**: {e.snippet}")
                else:
                    st.write("No evidence captured.")

                # Optional verification metadata
                if getattr(f, "status", None):
                    st.markdown(f"**Status:** {f.status}")
                qrc = getattr(f, "quality_reason_codes", []) or []
                if qrc:
                    st.markdown("**Quality checks:**")
                    for r in qrc:
                        st.write(f"- {r}")

                rc = getattr(f, "reg_citations", []) or []
                if rc:
                    st.markdown("**Regulation citations (raw):**")
                    st.json(rc[:3])

    st.divider()

    # --- Raw JSON ---
    with st.expander("Raw JSON output", expanded=False):
        st.code(result.model_dump_json(indent=2), language="json")
        st.download_button(
            "Download JSON",
            data=result.model_dump_json(indent=2),
            file_name="analysis_result.json",
            mime="application/json",
        )
