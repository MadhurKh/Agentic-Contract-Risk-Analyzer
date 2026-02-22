# Patch: Fix executive score blank + reduce noisy findings (Covered/Partial/Gap) + dedupe

## Symptoms addressed
1) Executive scorecard score shown blank in UI:
   - UI versions differ; some expect `score` or `overall_score`.
   - Reviewer now returns multiple aliases: `score`, `overall_score`, and canonical `overall_score_0_100`.

2) Findings were repetitive and almost all "Potential gap":
   - Auditor now classifies each obligation vs clause as:
     - COVERED (suppressed; no finding)
     - PARTIAL (finding with downshifted severity)
     - GAP (finding)
   - Deterministic lexical overlap heuristic; no LLM required.

3) 23+ duplicates:
   - Dedupe findings by (jurisdiction, obligation_id), keeping the highest severity/confidence/grounding instance.
   - Adds `related_clause_ids` to preserve traceability.

## Files changed
- src/agents/reviewer.py
- src/agents/auditor.py

## Run
- python -m pytest -q
- streamlit run streamlit_ui/dashboard.py
