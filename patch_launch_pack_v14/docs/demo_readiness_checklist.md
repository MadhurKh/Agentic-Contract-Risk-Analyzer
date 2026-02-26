# Demo Readiness Checklist (GitHub + Live Demo + LinkedIn)

## A) GitHub readiness (5–10 min)

- [ ] `README.md` has:
  - [ ] one-line pitch + differentiator (“Local PDFs only” grounding)
  - [ ] quickstart (Windows)
  - [ ] build index instructions
  - [ ] link to `docs/architecture.md`
- [ ] `.gitignore` excludes:
  - [ ] `outputs/`
  - [ ] `data/regulations/**` (PDFs are large / licensed)
  - [ ] `data/rag_index/**` (optional, recommended)
- [ ] Repo has:
  - [ ] `docs/architecture.md` + diagram
  - [ ] `docs/runbook.md`
  - [ ] `docs/hiring_manager_pack/` (one-pager + demo script + DS handshake + architecture)

## B) Demo readiness (10–15 min)

- [ ] Build index: `py scripts\build_reg_index.py`
- [ ] Run UI: `py -m streamlit run streamlit_ui\dashboard.py`
- [ ] Use sample contract
- [ ] Toggle: Agentic ON, Require citations ON, Jurisdictions EU + AU
- [ ] Confirm:
  - [ ] Findings show clause evidence
  - [ ] Citations show doc/page/excerpt
  - [ ] Verified > 0 (ideally majority)
  - [ ] Raw JSON renders

## C) Screenshots (5 min)

Capture 3 screenshots and store in `docs/assets/`:

1) `ui_overview.png` — Title + metrics + Executive Summary + Top Risks
2) `finding_with_citations.png` — One finding expanded showing evidence + citations
3) `raw_json.png` — Raw JSON expander open showing schema output

Optional:
- `architecture.png` already exists in `docs/assets/`.

## D) LinkedIn post (10 min)

- [ ] Use `docs/linkedin_post.md`
- [ ] Attach 2–3 screenshots (or a 30–60 sec screen recording)
- [ ] Post + pin
