# Local PDFs Only — Grounding & Citations

## Non-negotiable constraint
Regulation citations must come from **local PDFs only** (no web retrieval).

## Local regulation folders
- EU:
  - `data/regulations/eu_ai_act/`
- Australia:
  - `data/regulations/australia/`

## Index location
- `data/rag_index/reg_index.pkl`

## Build / rebuild the index
- Windows: `build_reg_index.bat`
- Or:
  - `python scripts/build_reg_index.py`

## Demo / verification implications
- When “Require regulation citations” is ON:
  - Findings are VERIFIED only when citations + grounding pass thresholds.
- If verified counts drop unexpectedly:
  - First check that the index exists and matches selected jurisdictions (EU/AU).
