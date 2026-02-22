from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Simple stdlib logger factory (used across the repo)
_LOGGERS: Dict[str, logging.Logger] = {}

def get_logger(name: str = "agentic_contract_risk_analyzer") -> logging.Logger:
    if name in _LOGGERS:
        return _LOGGERS[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    _LOGGERS[name] = logger
    return logger


def save_run(run_id: str, payload: Dict[str, Any]) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = LOG_DIR / f"{ts}_{run_id}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
