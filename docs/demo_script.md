# Demo Script — Agentic Contract Risk Analyzer (Local PDFs Only)

## 30–45 seconds (quick)
- “This is an **Agentic Contract Risk Analyzer** built as a **Streamlit app**.”
- “It takes a contract (sample / paste / upload) and runs an **agent pipeline**: Extractor → Obligation Mapper → Auditor → Verifier → Reviewer.”
- “The key constraint is **Local PDFs only** for regulation grounding — **no web RAG**.”
- “The output is a **risk score (0–100)**, **risk level**, **Top Risks**, and **Findings** with **evidence + citations** from the local regulation PDFs.”
- “We also provide a **Raw JSON export** for auditability and downstream integration.”

## 90–120 seconds (full)
1) **Set up the run**
   - Select **Sample contract** (or paste/upload).
   - Turn **Agentic mode ON**.
   - Turn **Require regulation citations (local PDFs) ON**.
   - Select jurisdictions (**EU**, **AU**).

2) **What’s happening under the hood**
   - **Extractor** identifies clauses/signals from the contract.
   - **Obligation Mapper** maps signals to an **EU + AU obligation catalog**.
   - **Auditor** grounds each mapped obligation using **local PDF RAG** (pre-built index).
   - **Verifier** checks grounding quality and citation presence.
   - **Reviewer** produces a structured scorecard + statuses (VERIFIED / NEEDS_REVIEW).

3) **What to show in the UI**
   - **Executive Summary** for the headline outputs.
   - **Top Risks** for the short list executives care about.
   - **Findings** expanders for clause-level detail and citations.
   - **Raw JSON (debug/export)** for audit trail.

## Suggested “demo closer”
- “This is designed to be **production-friendly**: local-only citations, deterministic exports, and a clear audit trail for compliance reviews.”
