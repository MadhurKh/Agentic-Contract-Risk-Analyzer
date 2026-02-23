# Patch: Fix mid-word truncation (Executive Scorecard + Top Risks)

## What this patch fixes
- Removes hard slicing (`[:60]`) that was cutting words mid-sentence in `Top Risks`.
- Replaces reviewer truncation helper with word-boundary truncation + ellipsis (`…`).

## Files included
- `src/orchestrator.py`
- `src/reviewer.py` (if your project keeps reviewer here)
- `src/agents/reviewer.py` (recommended location)

## Apply
1. Copy `src/orchestrator.py` into your repo `src/orchestrator.py`.
2. Place reviewer in **one** place:
   - If your imports are `from src.reviewer import ...` keep `src/reviewer.py`, OR
   - If you prefer agent structure, use `src/agents/reviewer.py` and update imports accordingly.
3. Restart Streamlit.

## Notes on reviewer location
- If you move reviewer under `src/agents/`, make sure `src/agents/__init__.py` exists and update imports:
  - Example: `from src.agents.reviewer import review_findings`
