# DS ↔ Engineering Handshake (How I collaborate with Data Science)

## Stable interface
- UI calls a single adapter: `analyze_contract(contract_text, title, source_type)`
- Adapter returns a strict schema: `AnalysisResult` (Pydantic)

## Feature-first pipeline
1) Parse → extract features (`src/feature_extractor.py`)
2) Generate findings (rules/LLM/ML)
3) Compute score + explainability (`src/scoring.py`)
4) Return schema-valid result + audit log

## Explainable scoring (DS-tunable)
- Severity weights and aggregation
- Threshold mapping score → risk level
- Scoring breakdown returned in output for transparency

## Evaluation hooks
- Unit tests for schema invariants, evidence requirement, and scoring monotonicity
- Harness stub can be expanded to labeled datasets
- Versioning supports reproducibility (model/prompt/ruleset)