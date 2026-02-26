# FAQ

## Why does the export script fail with “No module named pydantic”?
It is using a different Python interpreter than your `.venv`. Use `run_export_demo.bat` which prefers `.venv\Scripts\python.exe`.

## Should I commit regulation PDFs to GitHub?
No. Regulations PDFs can be large and may have licensing restrictions. Keep them local and add to `.gitignore`.

## What should be committed?
- Source code
- Sample contracts (text)
- Scripts to build the index
- Documentation and demo assets (screenshots you own)

## What should NOT be committed?
- `data/regulations/**`
- `data/rag_index/**` (rebuildable)
- `outputs/**` (exports)
- `.env*`, `.venv`, logs
