# Hiring Manager Quick Pack — GenAI Contract Risk Analyzer

## What this is
A portfolio demo showing an enterprise-style GenAI application with:
- structured outputs (risk register + evidence),
- DS handshake layer (features extracted),
- explainable scoring breakdown,
- audit log + exportable JSON.

## Watch the demo (2 minutes)
- Video: https://drive.google.com/file/d/12sLuSNMl59imbLOYdIYgVAPFbO6yn9TY/view?usp=drive_link

## Review in 60 seconds
- Streamlit UI: `streamlit_ui/dashboard.py`
- Adapter boundary: `src/model_adapter.py::analyze_contract()`
- Schemas (contract): `src/schemas.py`
- Feature extraction: `src/feature_extractor.py`
- Scoring logic: `src/scoring.py`
- Tests: `tests/`

## Run it locally (Windows)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m streamlit run streamlit_ui\dashboard.py