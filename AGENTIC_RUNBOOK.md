# Agentic Contract Risk Analyzer — MVP Runbook

## 1) Run baseline UI
```powershell
.\.venv\Scripts\activate
streamlit run streamlit_ui\dashboard.py
```

## 2) Enable Agentic mode
Use the sidebar toggle **Agentic mode (5-agent)**.
- If enabled, UI sets `USE_AGENTIC=1` for the session.

## 3) Add regulation PDFs + build RAG index
Place PDFs under:
- `data/regulations/eu_ai_act/`
- `data/regulations/australia/`

Build index:
```powershell
python scripts\build_reg_index.py
```

## 4) Rerun analysis
- If index exists, Auditor attaches citations and Verifier can mark findings VERIFIED.
