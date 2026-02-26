# Architecture Diagram — Agentic Contract Risk Analyzer

This diagram captures the end-to-end execution flow and the hard constraint that **all regulation citations are grounded from local PDFs only** (no web retrieval).

## Diagram

![Architecture](assets/architecture.png)

- Vector version (for docs / slides): `docs/assets/architecture.svg`

## Execution Flow (Agentic Mode)

1. **Streamlit UI** collects input (sample/paste/upload) + run toggles (agentic + require citations) and jurisdictions (EU/AU).
2. UI calls the **stable adapter boundary**: `src/model_adapter.py::analyze_contract(...)`.
3. In agentic mode, the adapter routes to `src/orchestrator.py::run_agentic_contract_analysis(...)`.
4. The orchestrator runs the agent sequence:
   - **Extractor** → clause segmentation + evidence spans
   - **Obligation Mapper** → maps clauses to applicable obligations (EU + AU catalog)
   - **Auditor (Local RAG)** → retrieves regulation snippets from the **local-only** RAG index
   - **Verifier** → applies quality gate (evidence + citations + grounding)
   - **Reviewer** → aggregates scorecard + executive summary + audit events
5. Output is a schema-validated `AnalysisResult` (Pydantic) returned to UI.
6. UI uses `src/ui_view_model.py` to render a demo-ready view (score, summary, top risks, findings accordion) and “Raw JSON”.

## Local-PDF-Only Regulation Grounding

- Regulation PDFs live under: `data/regulations/...`
- The local RAG index is built into: `data/rag_index/reg_index.pkl`
- The auditor must use this local index when citations are required.

## Export / Demo Snapshots (Headless)

For portfolio / demos, a CLI runner exports the schema-validated JSON without running Streamlit:

- Runner: `scripts/run_export_demo.py` + `run_export_demo.bat`
- Output: `outputs/latest_demo_run.json` (and timestamped snapshots)
