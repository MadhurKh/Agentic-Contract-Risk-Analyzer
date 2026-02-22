# Runbook --- GenAI Contract Risk Analyzer

## Quick Start (Windows)

py -m venv .venv ..venv`\Scripts`{=tex}`\Activate`{=tex}.ps1 py -m pip
install -r requirements.txt py -m streamlit run
streamlit_ui`\dashboard`{=tex}.py

Open: http://localhost:8501

## Common Issues

### 1. ModuleNotFoundError: 'src'

Ensure you are running from repository root.

### 2. Sample contracts not showing

Ensure files are in: sample_data/ or sample_data/contracts/

### 3. RAG Index Not Found

Rebuild or verify: data/rag_index/

## Governance Notes

-   Contracts may contain sensitive data.
-   Add redaction before external deployment.
-   Ensure schema validity before export.
