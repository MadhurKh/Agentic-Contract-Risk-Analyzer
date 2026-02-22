# GenAI Contract Risk Analyzer --- Hiring Manager One-Pager

## What this is

A working, enterprise-style GenAI contract review system that converts
unstructured contract text into structured, explainable, audit-ready
outputs.

It demonstrates how to build a production-oriented AI system --- not
just a prompt demo.

## Core Capabilities

-   Risk score (0--100) + mapped risk level (Low / Medium / High /
    Critical)
-   Structured risk register (findings) with clause evidence
-   Multi-agent execution mode (Extractor → Obligation Mapper → Auditor
    → Verifier → Reviewer)
-   Explainable scoring breakdown (severity, thresholds, aggregation)
-   Optional regulation grounding via RAG index
-   Exportable JSON (schema-validated)
-   Audit log for traceability

## Enterprise Design Principles

### 1. Stable Adapter Boundary

UI depends on a single interface:
`src/model_adapter.py::analyze_contract()`

Modeling logic can evolve independently.

### 2. Strict Output Schema

Pydantic contracts defined in `src/schemas.py`. Enforced structure
reduces downstream integration risk.

### 3. Traceability

Every finding links to contract clause evidence. Version metadata +
audit log included.

### 4. Explainability

Scoring logic is deterministic and transparent. Severity weights and
thresholds are explicit.

### 5. Testability

Unit tests validate schema invariants and scoring logic.

## Where Data Science Fits

Data Science can iterate on: - Feature extraction logic - Obligation
detection (rules / LLM / ML) - Scoring calibration - RAG grounding
improvements - Risk threshold tuning

Engineering/UI remains stable because the adapter contract is enforced.

## Repository Map

-   UI: `streamlit_ui/dashboard.py`
-   Adapter: `src/model_adapter.py`
-   Features: `src/feature_extractor.py`
-   Scoring: `src/scoring.py`
-   Schemas: `src/schemas.py`
-   Tests: `tests/`
-   Data Contract: `docs/data_contract.md`
-   Modeling Contract: `docs/modeling_contract.md`
