# Hiring Manager Quick Pack --- GenAI Contract Risk Analyzer

## What this demonstrates

A production-oriented GenAI system with: - Multi-agent execution
pipeline - Structured risk register with clause evidence - Explainable
risk scoring - Verifier layer (quality control) - Optional regulation
grounding (RAG) - Exportable schema-validated JSON - Audit log for
traceability

This is structured like an enterprise integration --- not a prompt demo.

## 2-Minute Demo Video

https://drive.google.com/file/d/12sLuSNMl59imbLOYdIYgVAPFbO6yn9TY/view?usp=drive_link

## Review in 60 Seconds

-   UI: `streamlit_ui/dashboard.py`
-   Adapter boundary: `src/model_adapter.py::analyze_contract()`
-   Schemas: `src/schemas.py`
-   Feature extraction: `src/feature_extractor.py`
-   Scoring logic: `src/scoring.py`
-   Tests: `tests/`

## Run Locally (Windows)

py -m venv .venv ..venv`\Scripts`{=tex}`\Activate`{=tex}.ps1 py -m pip
install -r requirements.txt py -m streamlit run
streamlit_ui`\dashboard`{=tex}.py
