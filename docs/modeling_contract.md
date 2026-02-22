# Modeling Contract (Data Science ↔ Engineering)

## Objective

Produce enterprise-ready structured outputs: - Normalized Risk Score
(0--100) - Risk Level (Low/Medium/High/Critical) - Structured Risk
Register with evidence - Feature layer (DS handshake) - Explainable
scoring breakdown - Audit events

## Scoring Logic

points_i = severity_weight(severity_i) \* confidence_i total_points =
sum(points_i) score_0\_100 = normalize(total_points)

Data Science owns: - severity weights - thresholds mapping score → risk
level - calibration strategy (if ML introduced)

Engineering owns: - schema enforcement - UI rendering - logging + audit

## Feature Layer

Implemented in `src/feature_extractor.py`. Used for: - ML model input -
prompt conditioning - monitoring + drift analysis

## Evaluation (Future Production Step)

-   Labeled dataset
-   Precision/Recall/F1 by severity
-   Calibration metrics
-   False positive tracking

## Versioning Recommendation

Add explicit: - model_version - prompt_version - ruleset_version -
dataset_version (for evaluation runs)
