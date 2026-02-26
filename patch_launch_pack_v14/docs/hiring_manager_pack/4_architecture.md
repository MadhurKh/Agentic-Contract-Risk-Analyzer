# 4 — Architecture (Hiring Manager Summary)

This repo demonstrates a production-style pattern for Agentic AI:

1) **Stable Adapter Contract**
- UI calls `src/model_adapter.py::analyze_contract()`
- Output is a schema-validated `AnalysisResult` (Pydantic)

2) **Agent Orchestration**
- `src/orchestrator.py` runs a staged pipeline:
  Extractor → Obligation Mapper → Auditor → Verifier → Reviewer

3) **Local-PDF-only Grounding**
- Regulatory citations are retrieved from a local TF‑IDF index built from PDFs under `data/regulations/`
- No web retrieval is used for citations (reproducible, demo-safe)

4) **Deterministic Scoring + Export**
- Transparent severity weights + aggregation
- JSON export supports downstream system integration
