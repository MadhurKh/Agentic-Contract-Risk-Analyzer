from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ._common import AgentResult


@dataclass
class VerifierConfig:
    """Configuration for evidence/quality gate."""
    require_contract_evidence: bool = True
    require_reg_citations: bool = True
    min_confidence: float = 0.25


def run_verifier(*, findings: List[Dict[str, Any]], config: Optional[VerifierConfig] = None) -> AgentResult:
    """
    Agent 4 — Verifier (Evidence & Quality Gate)

    Enforces:
    - Each finding must have contract evidence (spans/snippets)
    - Each finding must have regulatory citations (when enabled)
    - Confidence threshold
    """
    config = config or VerifierConfig()

    verified: List[Dict[str, Any]] = []
    flags: List[Dict[str, Any]] = []

    for f in findings:
        reasons: List[str] = []
        if config.require_contract_evidence and not f.get("contract_evidence"):
            reasons.append("Missing contract evidence.")
        if config.require_reg_citations and not f.get("reg_citations"):
            reasons.append("Missing regulation citations.")
        if float(f.get("confidence", 0.0)) < config.min_confidence:
            reasons.append(f"Low confidence (<{config.min_confidence}).")

        if reasons:
            f2 = dict(f)
            f2["status"] = "NEEDS_REVIEW"
            f2["quality_reasons"] = reasons
            verified.append(f2)
            flags.append({"finding_id": f.get("finding_id"), "reasons": reasons})
        else:
            f2 = dict(f)
            f2["status"] = "VERIFIED"
            verified.append(f2)

    needs_review = any(v.get("status") == "NEEDS_REVIEW" for v in verified)
    return AgentResult(data={"verified_findings": verified, "quality_flags": flags, "needs_human_review": needs_review})
