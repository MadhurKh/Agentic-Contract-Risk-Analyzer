from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json
from pathlib import Path

from ._common import AgentResult


@dataclass
class ObligationMapperConfig:
    """Configuration for obligation mapping."""
    mode: str = "catalog"  # catalog | stub
    catalog_path: str = "src/regulation/obligations_catalog.json"


def _load_catalog(path: str) -> Dict[str, List[Dict[str, Any]]]:
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def run_obligation_mapper(*, jurisdiction: str, config: Optional[ObligationMapperConfig] = None) -> AgentResult:
    """
    Agent 2 — Obligation Mapper / Policy Interpreter

    Loads a curated catalog of normalized obligations per jurisdiction.
    """
    cfg = config or ObligationMapperConfig()
    j = jurisdiction.upper().strip()

    catalog = _load_catalog(cfg.catalog_path) if cfg.mode == "catalog" else {}
    obligations = catalog.get(j, [])

    if not obligations:
        # fallback minimal
        obligations = [
            {
                "obligation_id": f"{j}-OBL-001",
                "jurisdiction": j,
                "title": "Transparency & Disclosure",
                "requirement": "Provide appropriate transparency, disclosures, and documentation where required.",
                "applies_if": "AI/ML systems or automated decisioning is used in service delivery.",
                "severity_weight": 1.0,
            }
        ]

    # Normalize fields
    for o in obligations:
        o["jurisdiction"] = j
        o.setdefault("severity_weight", 1.0)

    return AgentResult(
        data={"jurisdiction": j, "obligations": obligations, "mode": cfg.mode},
        warnings=[] if cfg.mode == "catalog" else ["Obligation mapper running in stub mode."],
    )
