# Modeling Contract (Data Science ↔ Engineering)

## 1) Objective
Given contract text, the system produces **enterprise-friendly, machine-readable outputs**:
- Normalized **Risk Score (0–100)**
- Categorical **Risk Level** (Low/Medium/High/Critical)
- Structured **Risk Register** (findings with evidence + recommendations)
- **Features Extracted** (DS handshake layer)
- Explainable **Scoring Breakdown** (severity weights + per-finding points)
- **Audit Log** (events for traceability)

This is designed so Data Science can evolve modeling (rules/ML/LLM/RAG) without requiring Streamlit UI rewrites.

---

## 2) Inputs (UI → Adapter)
Primary:
- `contract_text: str`

Metadata (current):
- `title: str`
- `source_type: "paste" | "upload"`

**Source of truth (schema):** `src/schemas.py` (`ContractMeta`)

---

## 3) Outputs (Adapter → UI)
The adapter must return an object matching:
- `src/schemas.py::AnalysisResult`

Key fields:
- `run_id: str`
- `contract: ContractMeta`
- `summary: Summary` → `{ overall_risk_score, risk_level, top_risks[] }`
- `findings: List[Finding]` (each finding MUST include `evidence[]`)
- `features: FeatureSet` (structured feature vector for DS handoff)
- `scoring: ScoringBreakdown` (weights, total points, normalized score, per-finding breakdown)
- `audit: List[AuditEvent]` (pipeline events)

**Source of truth (schema):** `src/schemas.py`

---

## 4) Scoring / Thresholding (DS-owned)
Current scoring is explainable and deterministic:
- `src/scoring.py::compute_score()`

Method:
- `points_i = severity_weight(severity_i) * confidence_i`
- `total_points = Σ points_i`
- `score_0_100 = normalize(total_points)`

DS owns:
- severity weights (`Low/Medium/High/Critical`)
- thresholds mapping score → risk level
- any calibration strategy (e.g., isotonic regression, Platt scaling) if ML is introduced

Engineering owns:
- schema stability
- surfacing scoring breakdown in UI
- logging/auditability

---

## 5) Feature Layer (DS handshake)
Current implementation:
- `src/feature_extractor.py::extract_features()`

Purpose:
- produce a structured feature set (flags/counts) that can be:
  - consumed by an ML model (classifier/regression)
  - used for monitoring (data drift / rule hit-rate)
  - used for prompt conditioning (LLM pipelines)

DS owns:
- feature definitions and versioning strategy
- feature-to-label mapping for training datasets

---

## 6) Evaluation Hooks (DS-owned)
Recommended next steps for productionization:
- Labeled dataset of clauses/risks
- Offline evaluation harness

Suggested metrics:
- Precision / Recall / F1 by risk category + severity
- Calibration (score vs observed outcomes)
- False positive analysis for High/Critical findings

---

## 7) Versioning & Auditability (joint)
Current:
- `audit[]` captures pipeline events.

Recommended additions (future enhancement):
- `model_version`, `prompt_version`, `ruleset_version` as explicit fields
- dataset version (for evaluation runs)

Purpose:
- reproducibility, governance, model risk reviews

---

## 8) Deployment Notes (Engineering-owned)
- Output must remain schema-valid (no missing keys / wrong types)
- Errors must be handled gracefully (no UI crash)
- PII guidance: contracts may include personal data; add redaction rules if deploying beyond local demo