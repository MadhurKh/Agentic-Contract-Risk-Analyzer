from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ._common import AgentResult
from ..rag.retriever import retrieve
from ..rag.store import RagIndex


@dataclass
class AuditorConfig:
    mode: str = "tfidf_rag"
    top_k: int = 6
    min_hits_for_grounded: int = 1


def _mk_query(clause: Dict[str, Any], obligation: Dict[str, Any]) -> str:
    return (
        f"Obligation: {obligation.get('title','')} Requirement: {obligation.get('requirement','')} "
        f"Applies if: {obligation.get('applies_if','')} "
        f"Contract clause type: {clause.get('clause_type','')} "
        f"Clause text: {clause.get('clause_text','')[:900]}"
    )


def _severity_from(clause: Dict[str, Any], obligation: Dict[str, Any]) -> str:
    sd = (obligation.get("severity_default") or "").upper().strip()
    if sd in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        return sd
    ct = (clause.get("clause_type") or "").upper()
    if ct in {"SECURITY", "PRIVACY_DATA", "MODEL_RISK"}:
        return "HIGH"
    if ct in {"AUDIT_RIGHTS", "DATA_RETENTION", "HUMAN_OVERSIGHT", "LOGGING"}:
        return "MEDIUM"
    return "MEDIUM"


def _applicable_obligations_for_clause(clause: Dict[str, Any], obligations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ct = (clause.get("clause_type") or "").upper().strip()
    if not ct:
        return obligations
    out: List[Dict[str, Any]] = []
    for o in obligations:
        applicable = [str(x).upper().strip() for x in (o.get("clause_types_applicable") or [])]
        if not applicable or ct in applicable:
            out.append(o)
    return out


def run_auditor(
    *,
    clauses: List[Dict[str, Any]],
    obligations: List[Dict[str, Any]],
    rag_index: Optional[RagIndex] = None,
    config: Optional[AuditorConfig] = None,
) -> AgentResult:
    """Agent 3 — Auditor: filters obligations per clause to reduce noise."""
    cfg = config or AuditorConfig()
    findings: List[Dict[str, Any]] = []
    warnings: List[str] = []

    if not clauses:
        return AgentResult(data={"findings": [], "mode": cfg.mode}, warnings=["No clauses to audit."])

    if rag_index is None:
        warnings.append("RAG index not provided; regulatory citations will be missing.")

    for clause in clauses[:20]:
        applicable_obls = _applicable_obligations_for_clause(clause, obligations)
        if not applicable_obls:
            continue

        for obl in applicable_obls:
            juris = str(obl.get("jurisdiction", "")).upper().strip()
            reg_cits: List[Dict[str, Any]] = []

            if rag_index is not None:
                hits = retrieve(
                    query=_mk_query(clause, obl),
                    index=rag_index,
                    top_k=cfg.top_k,
                    filters={"jurisdiction": juris} if juris else None,
                )
                for h in hits:
                    reg_cits.append({
                        "doc_id": h.doc_id,
                        "chunk_id": h.chunk_id,
                        "page": h.meta.get("page"),
                        "title": h.meta.get("title"),
                        "text": h.text[:900],
                    })

            gap = (
                f"Potential gap vs obligation '{obl.get('title','')}' ({juris}). "
                f"Verify the clause includes explicit commitments matching the requirement."
            )

            sev = _severity_from(clause, obl)
            status = "DRAFT"
            confidence = 0.35

            if reg_cits and len(reg_cits) >= cfg.min_hits_for_grounded:
                confidence = 0.60
            else:
                status = "NEEDS_REVIEW"

            findings.append({
                "finding_id": f"F-{clause.get('clause_id','CL')}-{obl.get('obligation_id','OBL')}",
                "clause_id": clause.get("clause_id", "UNKNOWN"),
                "obligation_id": obl.get("obligation_id", "UNKNOWN"),
                "gap_statement": gap,
                "risk_category": "REGULATORY",
                "severity": sev,
                "confidence": confidence,
                "contract_evidence": clause.get("evidence_spans", []) or [],
                "reg_citations": reg_cits,
                "status": status,
                "jurisdiction": juris,
                "tags": obl.get("tags", []),
            })

    return AgentResult(data={"findings": findings, "mode": cfg.mode}, warnings=warnings)
