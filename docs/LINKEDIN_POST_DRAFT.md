# LinkedIn Post Draft — Agentic Contract Risk Analyzer (Local PDFs Only)

## Version A (crisp, outcome-first)
I built a demo: **Agentic Contract Risk Analyzer** — a Streamlit app that analyzes contract text and produces an executive-ready risk scorecard.

Key design choice (hard constraint): **regulation citations are grounded using LOCAL PDFs only** (no web RAG).
That means the evidence trail is auditable and works even in restricted enterprise environments.

What it does:
- Extracts contract clauses/signals
- Maps them to an **EU + AU obligation catalog**
- Grounds findings using a **local RAG index** over regulation PDFs
- Produces **Risk Score (0–100)**, **Risk Level**, **Top Risks**, and **Findings** with citations
- Exports a complete **Raw JSON audit trail**

If you’re working on “AI governance meets real enterprise constraints” — I’d love to compare notes.

#GenAI #AgenticAI #AICompliance #AIEngineering #RAG #Streamlit #Governance

## Version B (problem → solution → proof)
Most “contract risk” demos break when you ask: *where is the evidence?*  
So I built **Agentic Contract Risk Analyzer** with a strict constraint: **local-PDF-only regulation grounding** (no web RAG).

Pipeline: Extractor → Obligation Mapper → Auditor → Verifier → Reviewer  
Output: scorecard + top risks + findings with citations + JSON export.

This is intentionally shaped for enterprise realities: offline citations, audit trail, and repeatable exports.

#AgenticAI #Compliance #RAG #GenAI #AIProduct #Streamlit
