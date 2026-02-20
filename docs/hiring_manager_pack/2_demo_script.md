# 2–3 Minute Demo Script (Citi-ready)

## Goal
Show a working, enterprise-style GenAI demo with DS/Eng collaboration patterns: schema contracts, features layer, explainable scoring, evidence, audit log, export.

## Start
Run:
- `py -m streamlit run streamlit_ui/dashboard.py`
Open: `http://localhost:8501`

## Flow
1) Upload sample contract text
2) Show risk score + level + findings count
3) Expand a finding in Risk Register
4) Show extracted features (DS handshake)
5) Show scoring breakdown (weights + thresholds)
6) Show evidence snippet
7) Download JSON export

## Close statement (say this)
“The UI depends only on a stable adapter + strict schemas. DS can evolve modeling, calibration, and scoring behind the adapter without UI rewrites—exactly how we reduce integration risk in enterprise delivery.”