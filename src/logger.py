import json
from pathlib import Path
from datetime import datetime, timezone

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def save_run(run_id: str, payload: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = LOG_DIR / f"{ts}_{run_id}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path