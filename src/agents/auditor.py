from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import re

from ._common import AgentResult
from ..rag.retriever import retrieve
from ..rag.store import RagIndex, RagChunk
from ..utils.text import keyword_set, jaccard


@dataclass
class AuditorConfig:
    mode: str = "tfidf_rag"
    top_k: int = 8
    min_hits_for_grounded: int = 1
    rerank: bool = True
    max_citations_per_finding: int = 3

    # coverage heuristics (deterministic, no LLM)
    covered_threshold: float = 0.22
    partial_threshold: float = 0.12


_STOPWORDS = {
    "the","and","or","to","of","in","for","a","an","is","are","be","as","on","with","by","that","this",
    "will","shall","may","must","should","from","at","it","their","any","all","such"
}


def _mk_query(clause: Dict[str, Any], obligation: Dict[str, Any]) -> str:
    tags = " ".join([str(t) for t in (obligation.get("tags") or [])])
    return (
        f"{obligation.get('title','')} {obligation.get('requirement','')} {obligation.get('applies_if','')} "
        f"Tags: {tags}. "
        f"ClauseType: {clause.get('clause_type','')}. "
        f"Clause: {clause.get('clause_text','')[:900]}"
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


def _sev_downshift(sev: str) -> str:
    s = (sev or "MEDIUM").upper().strip()
    if s == "CRITICAL":
        return "HIGH"
    if s == "HIGH":
        return "MEDIUM"
    if s == "MEDIUM":
        return "LOW"
    return "LOW"


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


def _rerank_hits(hits: List[RagChunk], obligation: Dict[str, Any]) -> List[Tuple[RagChunk, float]]:
    q = " ".join([
        str(obligation.get("title","")),
        str(obligation.get("requirement","")),
        " ".join([str(t) for t in (obligation.get("tags") or [])]),
    ])
    qset = keyword_set(q, stop=_STOPWORDS)
    scored: List[Tuple[RagChunk, float]] = []
    for h in hits:
        hset = keyword_set(h.text, stop=_STOPWORDS)
        score = jaccard(qset, hset)
        scored.append((h, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def _dedupe_citations(cits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for c in cits:
        key = (c.get("doc_id"), c.get("page"), c.get("chunk_id"))
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def _coverage_score(clause_text: str, obligation: Dict[str, Any]) -> float:
    # deterministic overlap between obligation keywords and clause text keywords
    q = " ".join([
        str(obligation.get("title","")),
        str(obligation.get("requirement","")),
        str(obligation.get("applies_if","")),
        " ".join([str(t) for t in (obligation.get("tags") or [])]),
    ])
    qset = keyword_set(q, stop=_STOPWORDS)
    cset = keyword_set(clause_text or "", stop=_STOPWORDS)
    if not qset or not cset:
        return 0.0
    return jaccard(qset, cset)


def _coverage_label(score: float, cfg: AuditorConfig) -> str:
    if score >= cfg.covered_threshold:
        return "COVERED"
    if score >= cfg.partial_threshold:
        return "PARTIAL"
    return "GAP"


def _contract_evidence_from_clause(clause: Dict[str, Any]) -> List[Dict[str, Any]]:
    spans = clause.get("evidence_spans") or []
    if spans:
        return spans
    txt = (clause.get("clause_text") or "").strip()
    if not txt:
        return []
    snippet = txt[:260] + ("…" if len(txt) > 260 else "")
    return [{"clause_ref": clause.get("clause_id","N/A"), "snippet": snippet}]


def _sev_weight(sev: str) -> int:
    s = (sev or "MEDIUM").upper().strip()
    return {"LOW":1,"MEDIUM":2,"HIGH":3,"CRITICAL":4}.get(s, 2)


def run_auditor(
    *,
    clauses: List[Dict[str, Any]],
    obligations: List[Dict[str, Any]],
    rag_index: Optional[RagIndex] = None,
    config: Optional[AuditorConfig] = None,
) -> AgentResult:
    """Agent 3 — Auditor (RAG-grounded) with coverage classification + dedupe."""
    cfg = config or AuditorConfig()
    findings: List[Dict[str, Any]] = []
    warnings: List[str] = []

    if not clauses:
        return AgentResult(data={"findings": [], "mode": cfg.mode}, warnings=["No clauses to audit."])

    if rag_index is None:
        warnings.append("RAG index not provided; regulatory citations will be missing.")

    for clause in clauses[:25]:
        applicable_obls = _applicable_obligations_for_clause(clause, obligations)
        if not applicable_obls:
            continue

        clause_text = (clause.get("clause_text") or "")
        c_evidence = _contract_evidence_from_clause(clause)

        for obl in applicable_obls:
            juris = str(obl.get("jurisdiction", "")).upper().strip()
            reg_cits: List[Dict[str, Any]] = []

            # Coverage classification BEFORE creating a finding.
            cov_score = _coverage_score(clause_text, obl)
            cov = _coverage_label(cov_score, cfg)

            # If covered, suppress (no finding). This reduces noise and makes outputs look realistic.
            if cov == "COVERED":
                continue

            if rag_index is not None:
                hits = retrieve(
                    query=_mk_query(clause, obl),
                    index=rag_index,
                    top_k=cfg.top_k,
                    filters={"jurisdiction": juris} if juris else None,
                )
                if cfg.rerank and hits:
                    ranked = _rerank_hits(hits, obl)
                    hits = [h for h,_ in ranked]

                for h in hits:
                    reg_cits.append({
                        "doc_id": h.doc_id,
                        "chunk_id": h.chunk_id,
                        "page": h.meta.get("page"),
                        "title": h.meta.get("title"),
                        "excerpt": h.text[:700],
                    })

                reg_cits = _dedupe_citations(reg_cits)[: cfg.max_citations_per_finding]

            sev = _severity_from(clause, obl)
            if cov == "PARTIAL":
                sev = _sev_downshift(sev)

            # confidence: base + grounded + coverage signal
            confidence = 0.30
            if reg_cits and len(reg_cits) >= cfg.min_hits_for_grounded:
                confidence = 0.60
            confidence += 0.15 if cov == "PARTIAL" else 0.0
            confidence = min(0.85, confidence)

            status = "DRAFT"
            if not c_evidence:
                status = "NEEDS_REVIEW"
            elif not reg_cits and cfg.min_hits_for_grounded > 0:
                status = "NEEDS_REVIEW"

            if cov == "PARTIAL":
                gap = (
                    f"Partial alignment vs obligation '{obl.get('title','')}' ({juris}). "
                    f"Clause mentions related controls but may miss: {obl.get('requirement','')}"
                )
            else:
                gap = (
                    f"Potential gap vs obligation '{obl.get('title','')}' ({juris}). "
                    f"Verify the clause includes explicit commitments matching: {obl.get('requirement','')}"
                )

            findings.append({
                "finding_id": f"F-{clause.get('clause_id','CL')}-{obl.get('obligation_id','OBL')}",
                "clause_id": clause.get("clause_id", "UNKNOWN"),
                "obligation_id": obl.get("obligation_id", "UNKNOWN"),
                "gap_statement": gap,
                "risk_category": "REGULATORY",
                "coverage": cov,
                "coverage_score": round(float(cov_score), 3),
                "severity": sev,
                "confidence": round(float(confidence), 2),
                "contract_evidence": c_evidence,
                "reg_citations": reg_cits,
                "status": status,
                "jurisdiction": juris,
                "tags": obl.get("tags", []),
            })

    # Dedupe: keep worst/most grounded per (jurisdiction, obligation_id)
    best: Dict[tuple, Dict[str, Any]] = {}
    for f in findings:
        key = (f.get("jurisdiction"), f.get("obligation_id"))
        if key not in best:
            best[key] = f
            best[key]["related_clause_ids"] = [f.get("clause_id")]
            continue
        cur = best[key]
        cur_w = (_sev_weight(cur.get("severity")) , float(cur.get("confidence",0.0)), 1 if (cur.get("reg_citations") or []) else 0)
        new_w = (_sev_weight(f.get("severity")) , float(f.get("confidence",0.0)), 1 if (f.get("reg_citations") or []) else 0)
        if new_w > cur_w:
            f["related_clause_ids"] = list(set((cur.get("related_clause_ids") or []) + [f.get("clause_id")]))
            best[key] = f
        else:
            cur["related_clause_ids"] = list(set((cur.get("related_clause_ids") or []) + [f.get("clause_id")]))

    deduped = list(best.values())
    deduped.sort(key=lambda x: (_sev_weight(x.get("severity")), float(x.get("confidence",0.0))), reverse=True)

    return AgentResult(data={"findings": deduped, "mode": cfg.mode}, warnings=warnings)
