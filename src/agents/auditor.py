from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ._common import AgentResult
from ..rag.retriever import retrieve
from ..rag.store import RagIndex


@dataclass
class AuditorConfig:
    """Configuration for audit agent."""
    mode: str = "tfidf_rag"   # stub | tfidf_rag
    top_k: int = 5


def _mk_query(clause: Dict[str, Any], obligation: Dict[str, Any]) -> str:
    return (
        f"{obligation.get('title','')} {obligation.get('requirement','')} "
        f"Contract clause: {clause.get('clause_text','')[:600]}"
    )


def run_auditor(
    *,
    clauses: List[Dict[str, Any]],
    obligations: List[Dict[str, Any]],
    rag_index: Optional[RagIndex] = None,
    config: Optional[AuditorConfig] = None,
) -> AgentResult:
    """
    Agent 3 — Auditor (RAG)

    Deterministic TF-IDF RAG version:
    - retrieves top_k regulatory chunks per obligation+clause query
    - creates findings with citations referencing retrieved chunks

    NOTE: Gap statement is still template-based (no LLM yet).
    """
    config = config or AuditorConfig()

    findings: List[Dict[str, Any]] = []
    if not clauses:
        return AgentResult(data={"findings": [], "mode": config.mode}, warnings=["No clauses to audit."])

    for clause in clauses[:10]:
        for obl in obligations:
            reg_cits: List[Dict[str, Any]] = []
            if rag_index is not None:
                q = _mk_query(clause, obl)
                hits = retrieve(query=q, index=rag_index, top_k=config.top_k)
                for h in hits:
                    reg_cits.append({
                        "doc_id": h.doc_id,
                        "chunk_id": h.chunk_id,
                        "page": h.meta.get("page"),
                        "title": h.meta.get("title"),
                        "text": h.text[:800],
                    })

            gap = (
                f"Clause may not fully address obligation '{obl.get('title','')}'. "
                f"Check for explicit commitments aligned to regulatory requirements."
            )
            conf = 0.55 if reg_cits else 0.35

            findings.append({
                "finding_id": f"F-{clause.get('clause_id','CL')}-{obl.get('obligation_id','OBL')}",
                "clause_id": clause.get("clause_id", "UNKNOWN"),
                "obligation_id": obl.get("obligation_id", "UNKNOWN"),
                "gap_statement": gap,
                "risk_category": "REGULATORY",
                "severity": "MEDIUM",
                "confidence": conf,
                "contract_evidence": clause.get("evidence_spans", []) or [],
                "reg_citations": reg_cits,
                "status": "DRAFT",
            })

    warn = []
    if rag_index is None:
        warn.append("RAG index not provided; citations will be missing.")
    return AgentResult(data={"findings": findings, "mode": config.mode}, warnings=warn)
