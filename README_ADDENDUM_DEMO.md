# README Addendum — Demo & Local-PDF-Only Constraint

## What this project does
Agentic Contract Risk Analyzer is a Streamlit-based demo app that analyzes contract text and produces:
- Risk score (0–100) and risk level
- Top Risks (executive-ready)
- Findings with evidence + regulation citations (when available)
- Raw JSON export for auditability

## Local-PDF-only grounding (hard constraint)
Regulation citations are grounded using **local PDFs only** (no web RAG).
- Regulations are stored under `data/regulations/`
- A local index is built to `data/rag_index/reg_index.pkl`

## Quickstart (local)
1) Create and activate a virtual environment
2) Install requirements
3) Build regulation index (local PDFs):
   - `build_reg_index.bat`
4) Run app:
   - `streamlit run streamlit_ui/dashboard.py`

## Export JSON (headless)
- Run: `run_export_demo.bat`
- Output: `outputs/latest_demo_run.json`

## Repo hygiene (GitHub)
Do not commit:
- `data/regulations/**`
- `data/rag_index/**`
- `outputs/**`
