# Hiring Manager Quick Pack — Agentic Contract Risk Analyzer

## What this demonstrates

A production-oriented **Agentic AI** system with:

- Multi-agent execution pipeline (Extractor → Obligation Mapper → Auditor → Verifier → Reviewer)
- Structured, audit-ready risk register with clause evidence
- Explainable, deterministic scoring with a breakdown (not “opaque LLM output”)
- Optional regulation grounding using **Local PDFs only** (no web RAG)
- Schema-validated JSON export + audit log for traceability

This is structured like an enterprise integration — not a prompt demo.

## Review in 60 seconds

- UI: `streamlit_ui/dashboard.py`
- Adapter boundary: `src/model_adapter.py::analyze_contract()`
- Schemas: `src/schemas.py`
- Orchestrator: `src/orchestrator.py`
- Agents: `src/agents/*`
- RAG index: `src/rag/*`
- Scoring: `src/scoring.py`
- Tests: `tests/`

## Run Locally (Windows)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m streamlit run streamlit_ui\dashboard.py
```

## Build Regulation Index (Local PDFs only)

```powershell
py scripts\build_reg_index.py
```

Expected: `data/rag_index/reg_index.pkl`

## Export (JSON)

```powershell
run_export_demo.bat
```

Outputs: `outputs/latest_demo_run.json`
