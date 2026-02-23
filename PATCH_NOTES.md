# Patch: Fix truncated Top Risks / Executive summary strings

## What this fixes
- Prevents mid-word truncation in **Top risks** and **Executive Scorecard** summary strings by truncating at word boundaries and appending an ellipsis (…).

## Files changed
- `src/reviewer.py`
  - Added `_truncate_text()` helper.
  - Updated `_summarize_title()` to use safe truncation.

## How to apply
1. Unzip into repo root (so `src/reviewer.py` overwrites existing).
2. Restart Streamlit.
