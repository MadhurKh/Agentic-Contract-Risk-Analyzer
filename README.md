
# Agentic Contract Risk Analyzer

A multi-agent AI system that evaluates contracts against regulatory obligations (EU AI Act, Australian frameworks) using clause extraction, obligation mapping, RAG-based regulatory grounding, verification, and executive scoring.

This project demonstrates how Agentic AI can move beyond prompt-based analysis into structured, auditable, multi-stage reasoning pipelines.

---

## 🚀 What Makes This Different?

Unlike traditional GenAI contract analyzers that rely on a single LLM pass, this system:

- Uses a 5-Agent Orchestration Pipeline
- Grounds findings using regulatory PDFs via RAG (TF-IDF index)
- Filters obligations per clause type (reduces noisy cross-product analysis)
- Verifies evidence and citations before marking findings as validated
- Produces an Executive Risk Scorecard

---

## 🧠 Architecture Overview (5-Agent System)

### 1️⃣ Extractor Agent
- Splits contract into structured clauses
- Assigns clause types (SECURITY, PRIVACY_DATA, TRANSPARENCY, etc.)
- Captures evidence spans

### 2️⃣ Obligation Mapper Agent
- Loads curated regulatory obligations (EU AI Act, AU)
- Each obligation declares `clause_types_applicable`
- Reduces irrelevant comparisons

### 3️⃣ Auditor Agent (RAG-powered)
- Cross-checks clause vs relevant obligations
- Retrieves regulatory evidence from indexed PDFs
- Produces grounded findings with citations

### 4️⃣ Verifier Agent
- Enforces:
  - Contract evidence present
  - Regulatory citations present
  - Confidence threshold
- Flags findings as NEEDS_REVIEW when grounding is insufficient

### 5️⃣ Reviewer Agent
- Aggregates risk metrics
- Generates executive-ready Risk Scorecard
- Produces summary + next steps

---

## 📂 Project Structure

src/
  agents/
    extractor.py
    obligation_mapper.py
    auditor.py
    verifier.py
    reviewer.py
  rag/
    indexer.py
    retriever.py
    store.py
  regulation/
    obligations_catalog.json
  orchestrator.py
  model_adapter.py

streamlit_ui/
  dashboard.py

data/
  regulations/
    eu_ai_act/
    australia/
  rag_index/

tests/

---

## 🏗 How to Run

### 1️⃣ Install dependencies
pip install -r requirements.txt

### 2️⃣ Add Regulatory PDFs
Place official documents in:

data/regulations/eu_ai_act/
data/regulations/australia/

### 3️⃣ Build RAG Index
python scripts/build_reg_index.py

### 4️⃣ Launch UI
streamlit run streamlit_ui/dashboard.py

Enable:
- Agentic mode
- Require regulation citations

---

## 🧪 Testing

Run:

python -m pytest -q

Includes:
- Applicability filtering test
- Scoring monotonicity test
- Evaluation harness
- Model adapter smoke tests

---

## 📊 Example Output

- Overall Risk Score
- Risk Level
- Findings with:
  - Severity
  - Confidence
  - Contract Evidence
  - Regulatory Citations (page + excerpt)
- Executive Risk Scorecard
- Needs Human Review indicator

---

## 🎯 Why This Matters

This project demonstrates:

- Agentic AI system design
- Deterministic + explainable architecture
- Regulatory grounding (EU AI Act)
- Multi-stage reasoning instead of single-pass LLM output
- Enterprise-ready audit trail design

---

## ⚖️ Disclaimer

This tool is for educational and demonstration purposes.
It does not constitute legal advice.
Human legal review is always required.

---

## 👤 Author

Madhur Khandelwal  
AI Transformation | Agentic AI Systems | Regulatory-Aware AI Design

GitHub: https://github.com/MadhurKh
