# GenAI Contract Risk Analyzer — Hiring Manager One-Pager

## What it is
A working GenAI-style contract review demo that converts unstructured contract text into structured, audit-ready outputs:
- Risk score (0–100) + risk level
- Structured risk register (findings) with evidence
- Features extracted layer (DS ↔ Engineering handshake)
- Scoring breakdown (explainability)
- Exportable JSON (schema-valid)
- Audit log (events + version metadata)

## Why it matters (enterprise lens)
Designed like a production integration:
- Stable adapter boundary: UI calls one interface (`src/model_adapter.py::analyze_contract`)
- Strict schemas: source-of-truth in `src/schemas.py`
- Traceability: every finding includes clause evidence
- Explainability: scoring methodology + thresholds are explicit
- Testability: unit tests validate schema + scoring invariants

## Where Data Science fits
- DS iterates on feature extraction, scoring/calibration, and model/prompt logic behind the adapter
- Engineering/UI remains stable because the output contract is enforced

## Repo map
- UI: `streamlit_ui/dashboard.py`
- Adapter: `src/model_adapter.py`
- Features: `src/feature_extractor.py`
- Scoring: `src/scoring.py`
- Schemas: `src/schemas.py`
- Tests: `tests/`
- Data Contract: `docs/data_contract.md`
- Modeling Contract: `docs/modeling_contract.md`