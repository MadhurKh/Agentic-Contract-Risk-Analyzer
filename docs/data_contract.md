# Data + Model Interface Contract

## Input
- contract_text: string
- title: string
- source_type: paste | upload

## Output (AnalysisResult)
- run_id: string
- summary: overall_risk_score (0-100), risk_level, top_risks
- findings[]: category, severity, confidence, recommendation
- evidence[]: clause_ref + snippet (mandatory)

## Evidence rule
No finding is valid unless it includes at least one evidence snippet.

## Auditability
Every run logs:
- run_id
- timestamp
- output JSON
- (next) model + prompt version