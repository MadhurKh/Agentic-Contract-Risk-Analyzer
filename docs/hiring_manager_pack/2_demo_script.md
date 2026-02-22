# 2--3 Minute Demo Script (Enterprise Framing)

## Goal

Demonstrate a production-style GenAI system with: - Structured outputs -
Multi-agent pipeline - Explainable scoring - DS/Engineering separation -
Audit-ready traceability

## Start

Run: py -m streamlit run streamlit_ui/dashboard.py Open:
http://localhost:8501

## Demo Flow

### 1. Upload contract

Show: - Overall Risk Score - Risk Level - Findings count

Explain: "The system converts unstructured contract text into a
structured risk register with scoring."

### 2. Expand a Finding

Show: - Risk level - Obligation reference - Clause evidence - Reasoning

Say: "Each finding includes traceable clause evidence, enabling audit
defensibility."

### 3. Show Executive Scorecard

Explain: - Score aggregation - Severity mapping - Risk threshold logic

Say: "Scoring is deterministic and transparent --- not opaque LLM
output."

### 4. Toggle Agentic Mode

Explain the multi-agent structure: Extractor → Obligation Mapper →
Auditor → Verifier → Reviewer

### 5. Show JSON Export

Explain: "Output is schema-validated and API-ready for enterprise
integration."

## Close Statement

"The UI depends only on a stable adapter and strict schemas. Data
Science can evolve modeling behind that boundary without UI rewrites ---
reducing integration risk in enterprise AI delivery."
