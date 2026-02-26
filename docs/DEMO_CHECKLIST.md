# Demo Checklist (2-minute prep)

## Before the demo
- Confirm regulation PDFs are present:
  - `data/regulations/eu_ai_act/`
  - `data/regulations/australia/`
- Confirm the local regulation index exists:
  - `data/rag_index/reg_index.pkl`
  - If missing: run `build_reg_index.bat` (or `python scripts/build_reg_index.py`).
- Confirm the app runs:
  - `streamlit run streamlit_ui/dashboard.py`

## During the demo
- Use **Sample contract** for a fast, repeatable run.
- Keep these toggles:
  - Agentic mode: **ON**
  - Require regulation citations: **ON**
  - Jurisdictions: **EU + AU**
- Walk through:
  1) Executive Summary
  2) Score panel (risk level + score + verified)
  3) Top Risks (unique, non-repeating)
  4) Expand 1–2 Findings and point to citations
  5) Open Raw JSON (audit trail)

## After the demo
- Generate an export JSON (no UI required):
  - Run `run_export_demo.bat`
  - Use `outputs/latest_demo_run.json` for sharing internally (do not commit)
