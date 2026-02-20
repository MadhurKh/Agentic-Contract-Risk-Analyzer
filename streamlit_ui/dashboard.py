import json
import streamlit as st

from src.model_adapter import analyze_contract
from src.logger import save_run

st.set_page_config(page_title="GenAI Contract Risk Analyzer", layout="wide")

st.title("GenAI Contract Risk Analyzer (Portfolio Demo)")
st.caption("Enterprise-style outputs: schema contract, evidence, audit log, features, scoring breakdown, and exportable JSON.")

# --- Layout: Input (left) + Output (right) ---
left, right = st.columns([1.05, 0.95])

# --------------------
# LEFT: INPUT
# --------------------
with left:
    st.subheader("1) Provide contract text")

    input_type = st.radio("Input type", ["Paste text", "Upload .txt"], horizontal=True)
    contract_title = st.text_input("Contract title", value="Sample MSA")

    contract_text = ""
    source_type = "paste"

    if input_type == "Paste text":
        contract_text = st.text_area("Paste contract here", height=320)
        source_type = "paste"
    else:
        uploaded = st.file_uploader("Upload .txt contract", type=["txt"])
        if uploaded is not None:
            contract_text = uploaded.read().decode("utf-8", errors="ignore")
            source_type = "upload"
            st.success("File loaded successfully.")

    run_btn = st.button("Analyze contract", type="primary", disabled=(len(contract_text.strip()) == 0))

# --------------------
# RUN ANALYSIS
# --------------------
if run_btn:
    result_obj = analyze_contract(contract_text, title=contract_title, source_type=source_type)
    result = result_obj.model_dump()
    st.session_state["result"] = result

    # Save audit log to /logs
    save_run(result["run_id"], result)

# --------------------
# RIGHT: OUTPUT (Render INSIDE right column)
# --------------------
with right:
    st.subheader("2) Output")

    if "result" not in st.session_state:
        st.info("Run analysis to see results here.")
    else:
        data = st.session_state["result"]

        # Summary metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Overall Risk Score", data["summary"]["overall_risk_score"])
        m2.metric("Risk Level", data["summary"]["risk_level"])
        m3.metric("Findings", len(data["findings"]))

        st.divider()

        # Tabs
        tabs = ["Risk Register", "Evidence", "Features Extracted", "Scoring Logic", "Audit Log", "Data Contract"]
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tabs)

        with tab1:
            st.subheader("Risk Register")
            if len(data["findings"]) == 0:
                st.warning("No findings returned.")
            else:
                for f in data["findings"]:
                    title = f'{f["finding_id"]} | {f["category"]} | {f["severity"]}'
                    with st.expander(title, expanded=False):
                        st.write("**Risk statement:**", f["risk_statement"])
                        st.write("**Recommendation:**", f["recommendation"])
                        if f.get("proposed_redline"):
                            st.write("**Proposed redline:**", f["proposed_redline"])
                        st.write("**Confidence:**", f["confidence"])

        with tab2:
            st.subheader("Evidence (No claim without clause snippet)")
            if len(data["findings"]) == 0:
                st.info("Run analysis first.")
            else:
                ids = [f["finding_id"] for f in data["findings"]]
                selected = st.selectbox("Select a finding", options=ids)

                finding = next(x for x in data["findings"] if x["finding_id"] == selected)
                ev = finding.get("evidence", [])

                if not ev:
                    st.error("Evidence missing — needs review.")
                else:
                    for e in ev:
                        st.write(f'**{e["clause_ref"]}**')
                        st.code(e["snippet"])

        with tab3:
            st.subheader("Features Extracted (DS handshake layer)")
            features = data.get("features", {})
            feats = features.get("features", [])
            if not feats:
                st.info("No features returned.")
            else:
                st.dataframe(feats, use_container_width=True)

        with tab4:
            st.subheader("Scoring Logic (Explainability)")
            scoring = data.get("scoring", {})
            if not scoring:
                st.info("No scoring breakdown returned.")
            else:
                st.json(scoring)

        with tab5:
            st.subheader("Audit Log")
            st.json(data.get("audit", []))

            st.subheader("Download JSON")
            st.download_button(
                label="Download analysis.json",
                data=json.dumps(data, indent=2),
                file_name="analysis.json",
                mime="application/json",
            )

        with tab6:
            st.subheader("Data + Model Interface Contract (what engineers care about)")
            st.markdown(
                """
**Input**
- `contract_text` (string)
- `title` (string)
- `source_type` (`paste|upload`)

**Output (strict schema)**
- `run_id` (string)
- `summary` (risk score + level + top risks)
- `findings[]` (structured risk register)
- `evidence[]` inside each finding (**mandatory**)
- `features` (DS handshake feature set)
- `scoring` (explainable breakdown)
- `audit[]` events

**Evidence rule**
- No finding is valid unless it has at least one evidence snippet.
                """
            )