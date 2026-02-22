# Data + Model Interface Contract

## Input (UI → Adapter)

-   contract_text: string
-   title: string
-   source_type: "paste" \| "upload"

## Output (Adapter → UI)

The adapter must return an `AnalysisResult` (see `src/schemas.py`).

Core fields: - run_id: string - contract: metadata object - summary: -
overall_risk_score (0--100) - risk_level (Low/Medium/High/Critical) -
top_risks\[\] - findings\[\]: - id - category - severity - confidence -
recommendation - evidence\[\] (mandatory) - features: structured feature
set - scoring: scoring breakdown (weights + per-finding points) -
audit\[\]: pipeline events

## Evidence Rule

No finding is valid unless it includes at least one evidence snippet.

## Schema Stability Principle

UI must only depend on `AnalysisResult` schema. Modeling changes must
not alter output structure.

## Auditability

Each run logs: - run_id - timestamp - scoring summary - full JSON
output - (future) model_version / prompt_version / ruleset_version
