# GitHub Release Checklist (Demo-Ready)

## 1) Hygiene / safety
- Run: `apply_gitignore_patch.bat`
- Confirm these are NOT tracked:
  - `data/regulations/**`
  - `data/rag_index/**`
  - `outputs/**`
- If any were already committed earlier, remove them from git history before pushing.

## 2) Quick demo path
- Build index (local PDFs): `build_reg_index.bat`
- Run app: `streamlit run streamlit_ui/dashboard.py`

## 3) Export path
- Run export: `run_export_demo.bat`
- Create bundle (optional): `run_make_demo_bundle.bat`

## 4) README
- Merge content from `README_ADDENDUM_DEMO.md` into your `README.md`.

## 5) Screenshots
Add 2–3 screenshots to `docs/`:
- Main dashboard after run
- One expanded Finding showing citations
- Raw JSON expander

## 6) Push
- `git status` should be clean aside from expected source changes
- `git push` to GitHub

## 7) LinkedIn
Use `docs/LINKEDIN_POST_DRAFT.md` and attach 1–2 screenshots (no sensitive data).
