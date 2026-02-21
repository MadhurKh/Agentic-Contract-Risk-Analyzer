from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ._common import AgentResult


@dataclass
class ObligationMapperConfig:
    mode: str = "catalog"
    catalog_path: str = "src/regulation/obligations_catalog.json"
    clause_types: Optional[List[str]] = None


def _load_catalog(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Obligations catalog not found: {path}")
    return json.loads(p.read_text(encoding="utf-8"))


def run_obligation_mapper(*, jurisdiction: str, config: Optional[ObligationMapperConfig] = None) -> AgentResult:
    """Agent 2 — Obligation Mapper (curated local catalog)."""
    cfg = config or ObligationMapperConfig()
    cat = _load_catalog(cfg.catalog_path)

    juris = (jurisdiction or "").upper().strip()
    obligations: List[Dict[str, Any]] = []
    for o in cat.get("obligations", []):
        if str(o.get("jurisdiction", "")).upper().strip() != juris:
            continue
        obligations.append(o)

    if cfg.clause_types:
        want = {c.upper().strip() for c in cfg.clause_types}
        filtered: List[Dict[str, Any]] = []
        for o in obligations:
            applicable = {str(x).upper().strip() for x in (o.get("clause_types_applicable") or [])}
            if (not applicable) or (applicable & want):
                filtered.append(o)
        obligations = filtered

    return AgentResult(data={"obligations": obligations, "jurisdiction": juris, "mode": cfg.mode})
