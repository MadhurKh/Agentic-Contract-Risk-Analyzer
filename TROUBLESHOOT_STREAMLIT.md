# Troubleshooting Streamlit "Error" page

## 1) Run Streamlit from repo root
```powershell
cd C:\Git\Agentic-Contract-Risk-Analyzer
streamlit run streamlit_ui\dashboard.py
```

## 2) If you see a red "Something went wrong" page
Open the terminal where Streamlit is running and copy the **full stack trace**.

## 3) Quick checks
- Ensure venv is active: prompt starts with `(.venv)`
- Install deps:
```powershell
pip install -r requirements.txt
```

## 4) Agentic flag
If you enabled agentic mode:
```powershell
$env:USE_AGENTIC="1"
```
Try disabling to confirm baseline works:
```powershell
Remove-Item Env:USE_AGENTIC -ErrorAction SilentlyContinue
```

## 5) RAG index
If you want citations, add PDFs and build the index:
```powershell
python scripts\build_reg_index.py
```
