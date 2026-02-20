# 2–3 Minute Demo Script — GenAI Contract Risk Analyzer (Citi-ready)

## Goal (10 seconds)
Demonstrate an enterprise-style GenAI application that:
- Converts unstructured contract text into **structured, reviewable outputs**
- Produces audit-friendly artifacts (risk register, evidence, scoring breakdown, audit log, exportable JSON)
- Uses a DS-friendly interface contract so modeling can evolve without UI rewrites

---

## Setup (10 seconds)
1. Start the app:
   - `py -m streamlit run streamlit_ui/dashboard.py`
2. Open: `http://localhost:8501`

---

## Step 1 — Input (15 seconds)
- Paste a contract excerpt or upload a sample `.txt`.

**Say:**
“This takes raw contract text in the same format legal/procurement teams receive.”

---

## Step 2 — Executive Output Summary (20 seconds)
Point to:
- **Overall Risk Score (0–100)**
- **Risk Level**
- **Findings count**

**Say:**
“This produces structured outputs—this is not a chat response; it’s decision-support.”

---

## Step 3 — Risk Register (30 seconds)
Open **Risk Register**:
- Show each finding: category, severity, recommendation / mitigation

**Say:**
“Each finding is a structured risk register entry that can be reviewed, tracked, and exported.”

---

## Step 4 — Evidence (20 seconds)
Open **Evidence**:
- Show clause snippet tied to the finding

**Say:**
“Every claim is backed by evidence snippets to avoid black-box outputs.”

---

## Step 5 — Features Extracted (20 seconds)
Open **Features Extracted**:
- Show feature table (flags + counts)

**Say:**
“This is the DS handshake layer. The system exposes features explicitly so DS can plug in ML models or monitoring without touching the UI.”

---

## Step 6 — Scoring Logic (25 seconds)
Open **Scoring Logic**:
- Show weights + per-finding points

**Say:**
“The scoring is explainable: severity weights + confidence per finding, with a breakdown that’s reviewable and testable.”

---

## Step 7 — Auditability + Export (20 seconds)
Open **Audit Log** + download JSON

**Say:**
“This includes an audit trail and exportable JSON—useful for governance and integration.”

---

## Step 8 — Data Contract (15 seconds)
Open **Data Contract** tab.

**Say:**
“This is the interface contract between DS and Engineering: strict schemas for inputs/outputs so models can evolve safely.”

---

## How I work with Data Science (30–40 seconds) — address the concern directly
**Say (verbatim):**
“I work with Data Science through stable interfaces and explicit contracts:
- The UI calls a single adapter (`src/model_adapter.py`) and expects a strict schema (`src/schemas.py`).
- DS can replace the internals with rules/ML/LLM/RAG while keeping the same output contract.
- We align on feature definitions, severity weights, thresholds, and evaluation metrics documented in `docs/modeling_contract.md`.
This is the approach I use to lead teams where DS iteration happens safely without breaking product.”

---

## Close (10 seconds)
**Say:**
“Next steps to productionize are: add a labeled dataset, offline evaluation harness, CI checks, and deployment packaging with governance controls.”