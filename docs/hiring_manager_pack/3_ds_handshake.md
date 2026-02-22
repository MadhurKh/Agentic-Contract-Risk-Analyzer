# DS ↔ Engineering Collaboration Pattern

## Stable Interface

UI calls one function:

analyze_contract(contract_text, title, source_type)

Returns: AnalysisResult (Pydantic schema)

This ensures DS experimentation does not break UI or downstream
integrations.

## Feature-First Pipeline

1.  Parse contract text
2.  Extract structured features (`feature_extractor.py`)
3.  Map obligations
4.  Generate findings
5.  Compute score + breakdown
6.  Return schema-validated result + audit log

## Explainable Scoring Model

-   Severity weights (configurable)
-   Aggregation logic
-   Threshold mapping score → risk level
-   Breakdown returned in output

## Governance & Evaluation Hooks

-   Unit tests enforce schema invariants
-   Evidence required for findings
-   Scoring monotonicity checks
-   Version metadata supports reproducibility
-   RAG index grounding for regulation traceability
