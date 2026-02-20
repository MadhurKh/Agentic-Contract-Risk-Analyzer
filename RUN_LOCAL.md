# Run locally (Agentic repo)

## Create venv + install
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install pytest
```

## Run tests
```powershell
python -m pytest -q
```

## Run Streamlit
Your Streamlit entry file is **not** in repo root. Run it using the correct path:

```powershell
streamlit run streamlit_ui/dashboard.py
```

## Agentic flag (later)
We will enable the agentic orchestrator via:
```powershell
$env:USE_AGENTIC="1"
```
