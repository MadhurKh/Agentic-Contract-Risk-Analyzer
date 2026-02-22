from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ._common import AgentResult


@dataclass
class VerifierConfig:
    require_contract_evidence: bool = True
    require_reg_citations: bool = True
    min_confidence: float = 0.25


def run_verifier(*, findings: List[Dict[str, Any]], config: Optional[VerifierConfig] = None) -> AgentResult:
    """Quality gate for agent outputs.

    - Marks each finding as VERIFIED or NEEDS_REVIEW
    - Adds human-readable `quality_reasons` and machine-readable `quality_reason_codes`
    - Returns aggregated `reason_counts` for UI/scorecard explanations
    """
    cfg = config or VerifierConfig()

    verified: List[Dict[str, Any]] = []
    flags: List[Dict[str, Any]] = []

    reason_counts: Dict[str, int] = {
        "MISSING_CONTRACT_EVIDENCE": 0,
        "MISSING_REG_CITATIONS": 0,
        "LOW_CONFIDENCE": 0,
    }

    for f in findings:
        reasons: List[str] = []
        reason_codes: List[str] = []

        if cfg.require_contract_evidence and not f.get("contract_evidence"):
            reasons.append("Missing contract evidence span/snippet.")
            reason_codes.append("MISSING_CONTRACT_EVIDENCE")

        if cfg.require_reg_citations and not f.get("reg_citations"):
            reasons.append("Missing regulation citations (build/refresh RAG index and rerun).")
            reason_codes.append("MISSING_REG_CITATIONS")

        if float(f.get("confidence", 0.0)) < cfg.min_confidence:
            reasons.append(f"Low confidence (<{cfg.min_confidence}).")
            reason_codes.append("LOW_CONFIDENCE")

        for c in reason_codes:
            reason_counts[c] = reason_counts.get(c, 0) + 1

        f2 = dict(f)
        if reasons:
            f2["status"] = "NEEDS_REVIEW"
            f2["quality_reasons"] = reasons
            f2["quality_reason_codes"] = reason_codes
            flags.append({"finding_id": f.get("finding_id"), "reasons": reasons, "reason_codes": reason_codes})
        else:
            f2["status"] = "VERIFIED"
            f2["quality_reasons"] = []
            f2["quality_reason_codes"] = []
        verified.append(f2)

    needs_review = any(v.get("status") == "NEEDS_REVIEW" for v in verified)
    return AgentResult(
        data={
            "verified_findings": verified,
            "quality_flags": flags,
            "needs_human_review": needs_review,
            "reason_counts": reason_counts,
        }
    )
