# GenAI Contract Risk Analyzer (Portfolio Demo)

This project demonstrates how Generative AI can assist legal/procurement teams by reviewing contract text, identifying risk factors and missing protections, and producing **enterprise-style outputs**:
- Structured risk register (findings + evidence)
- Extracted feature set (DS handshake layer)
- Explainable scoring breakdown (severity weights + confidence)
- Audit log + exportable JSON

> Current implementation is rule-based for portability and transparency, but the repo is structured so a Data Science team can replace internals with an LLM/RAG/model pipeline **without changing the UI**.

---

## Demo video
- 2-minute walkthrough (Google Drive): https://drive.google.com/file/d/12sLuSNMl59imbLOYdIYgVAPFbO6yn9TY/view?usp=drive_link

## Quick Start (Windows)

### Prerequisites
- Python (installed via `py`)
- Git

### Setup + Run
```powershell
cd "C:\Git\GenAI-Contract-Risk-Analyzer"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m streamlit run streamlit_ui\dashboard.py

## Working model with Data Science (DS ↔ Engineering)

This repo is structured so Data Science can iterate on modeling without changing the Streamlit UI.

### Interface contract
- The Streamlit UI calls a single adapter: `src/model_adapter.py::analyze_contract()`
- The adapter returns a strict output schema: `src/schemas.py::AnalysisResult`

### Adapter boundary (why this matters)
- UI/Orchestration stays stable.
- DS can swap internals (rules → LLM/RAG → ML) behind the adapter without breaking UI.

### Ownership (RACI)
- **Data Science owns:** feature definitions, labels, scoring logic, thresholds/calibration, offline evaluation, model/prompt versions
- **Engineering/Product owns:** UI, schema validation, logging/auditability, configuration, deployment readiness

### Contracts
- Data Contract: `docs/data_contract.md`
- Modeling Contract: `docs/modeling_contract.md`
- Hiring Manager Pack: `docs/hiring_manager_pack/`

### Auditability
- Output includes version metadata and an audit log for traceability.