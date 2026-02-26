from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ._common import AgentResult


@dataclass
class VerifierConfig:
    require_contract_evidence: bool = True
    require_reg_citations: bool = True
    min_confidence: float = 0.25
    # NEW: if auditor provides grounding_score, treat very low grounding as needs review
    min_grounding_score: float = 0.08


def run_verifier(*, findings: List[Dict[str, Any]], config: Optional[VerifierConfig] = None) -> AgentResult:
    cfg = config or VerifierConfig()

    verified: List[Dict[str, Any]] = []
    flags: List[Dict[str, Any]] = []

    for f in findings:
        reasons: List[str] = []
        if cfg.require_contract_evidence and not f.get("contract_evidence"):
            reasons.append("Missing contract evidence span/snippet.")
        if cfg.require_reg_citations and not f.get("reg_citations"):
            reasons.append("Missing regulation citations (build RAG index and rerun).")
        if float(f.get("confidence", 0.0)) < cfg.min_confidence:
            reasons.append(f"Low confidence (<{cfg.min_confidence}).")

        # Grounding quality gate (only if citations are required and a score is present)
        if cfg.require_reg_citations:
            gs = f.get("grounding_score", None)
            try:
                gs_f = float(gs) if gs is not None else None
            except Exception:
                gs_f = None
            if gs_f is not None and gs_f < cfg.min_grounding_score:
                reasons.append("Weak grounding to cited regulation text (low overlap).")

        f2 = dict(f)
        if reasons:
            f2["status"] = "NEEDS_REVIEW"
            f2["quality_reasons"] = reasons
            flags.append({"finding_id": f.get("finding_id"), "reasons": reasons})
        else:
            f2["status"] = "VERIFIED"
        verified.append(f2)

    needs_review = any(v.get("status") == "NEEDS_REVIEW" for v in verified)
    return AgentResult(data={"verified_findings": verified, "quality_flags": flags, "needs_human_review": needs_review})
