# Runbook — Agentic Contract Risk Analyzer

## Quick Start (Windows)

1) Create & activate virtual environment (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies

```powershell
py -m pip install -r requirements.txt
```

3) Launch UI

```powershell
py -m streamlit run streamlit_ui\dashboard.py
```

Open: http://localhost:8501

## Build the Local-PDF Regulation Index (Local PDFs only)

Place PDFs under:

- `data/regulations/eu_ai_act/`
- `data/regulations/australia/`

Then build the index:

```powershell
py scripts\build_reg_index.py
```

Expected output: `data/rag_index/reg_index.pkl`

## Export a Demo Run (JSON)

```powershell
run_export_demo.bat
```

Outputs:

- `outputs/latest_demo_run.json`
- `outputs/demo_run_YYYYMMDD_HHMMSS.json`

## Common Issues

### 1) ModuleNotFoundError: 'src'

- Ensure you run from repository root.
- Ensure `streamlit_ui/dashboard.py` adds repo root to `sys.path` (already included in this repo).

### 2) Sample contracts not showing

Ensure files exist in `sample_data/` as `.txt`.

### 3) RAG Index Not Found / No citations

- Confirm `data/rag_index/reg_index.pkl` exists.
- Rebuild index with `py scripts\build_reg_index.py`.
- Ensure jurisdiction tags are `EU` and `AU` in the index metadata.

## Governance Notes

- Contracts may contain sensitive data — redact before external sharing.
- Outputs are **not legal advice** — human review is required.
