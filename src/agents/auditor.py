from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ._common import AgentResult
from ..rag.retriever import retrieve
from ..rag.store import RagIndex, RagChunk
from ..utils.text import keyword_set, jaccard


@dataclass
class AuditorConfig:
    mode: str = "tfidf_rag"
    # Increased slightly: gives reranker more candidates to choose from, improves grounding stability
    top_k: int = 12
    min_hits_for_grounded: int = 1
    rerank: bool = True
    max_citations_per_finding: int = 3
    # Grounding thresholds (0-1) based on lexical overlap heuristic
    grounding_weak: float = 0.08
    grounding_moderate: float = 0.14
    grounding_strong: float = 0.22


_STOPWORDS = {
    "the","and","or","to","of","in","for","a","an","is","are","be","as","on","with","by","that","this",
    "will","shall","may","must","should","from","at","it","their","any","all","such",
    # extra legal filler that commonly dilutes keyword overlap
    "including","include","without","within","where","when","what","which","whose","thereof","hereby","therein",
    "party","parties","agreement","contract","clause","section","article","annex","schedule","appendix",
}


def _mk_query(clause: Dict[str, Any], obligation: Dict[str, Any]) -> str:
    # Add tags to improve retrieval, plus clause type
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


def _limit_tokens(tokens: set[str], max_n: int = 18) -> set[str]:
    """Keep the most-informative tokens to avoid denominator blow-ups.

    Jaccard is very sensitive to large unions; obligations often contain long requirement text.
    Keeping longer tokens generally preserves semantic signal (e.g., 'transparency', 'governance', 'notification').
    """
    if len(tokens) <= max_n:
        return tokens
    return set(sorted(tokens, key=lambda t: (len(t), t), reverse=True)[:max_n])


def _obligation_query_tokens(obligation: Dict[str, Any]) -> set[str]:
    title = str(obligation.get("title", ""))
    req = str(obligation.get("requirement", ""))
    tags = " ".join([str(t) for t in (obligation.get("tags") or [])])

    # Base keyword set
    q = " ".join([title, req, tags]).strip()
    qset = keyword_set(q, stop=_STOPWORDS)

    # Add obligation_id fragments (often encode domain keywords)
    obl_id = str(obligation.get("obligation_id", ""))
    if obl_id:
        parts = [p for p in re.split(r"[-_]+", obl_id.lower()) if p and p not in _STOPWORDS]
        for p in parts:
            if len(p) >= 3:
                qset.add(p)

    return _limit_tokens(qset, max_n=18)


def _overlap_score(qset: set[str], hset: set[str]) -> float:
    if not qset or not hset:
        return 0.0
    inter = len(qset & hset)
    # Coverage of query terms inside the hit (more stable than Jaccard when hit text is long)
    coverage = inter / max(1, len(qset))
    jac = jaccard(qset, hset)
    # Blend: coverage is primary signal; jaccard prevents over-crediting very small intersections.
    return float(0.75 * coverage + 0.25 * jac)


def _rerank_hits(hits: List[RagChunk], obligation: Dict[str, Any]) -> List[Tuple[RagChunk, float]]:
    # Improved lexical overlap between obligation keywords and chunk text.
    # Uses query-term coverage (intersection / |query|) blended with jaccard.
    qset = _obligation_query_tokens(obligation)

    scored: List[Tuple[RagChunk, float]] = []
    for h in hits:
        hset = keyword_set(h.text, stop=_STOPWORDS)
        score = _overlap_score(qset, hset)
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


def _grounding_level(score: float, cfg: AuditorConfig) -> str:
    if score >= cfg.grounding_strong:
        return "STRONG"
    if score >= cfg.grounding_moderate:
        return "MODERATE"
    if score >= cfg.grounding_weak:
        return "WEAK"
    return "NONE"


def _fmt_source(h: RagChunk) -> str:
    title = h.meta.get("title") or h.doc_id or "RegDoc"
    page = h.meta.get("page")
    if page is None or page == "":
        return str(title)
    return f"{title} (p.{page})"


def run_auditor(
    *,
    clauses: List[Dict[str, Any]],
    obligations: List[Dict[str, Any]],
    rag_index: Optional[RagIndex] = None,
    config: Optional[AuditorConfig] = None,
) -> AgentResult:
    """Agent 3 — Auditor (RAG-grounded).

    Output additions (non-breaking):
    - grounding_score (0..1): lexical overlap proxy for how well citations match obligation text
    - grounding_level: NONE/WEAK/MODERATE/STRONG
    - reg_citations[].score + reg_citations[].source for UI friendliness
    """
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

        for obl in applicable_obls:
            juris = str(obl.get("jurisdiction", "")).upper().strip()
            reg_cits: List[Dict[str, Any]] = []
            top_overlap = 0.0

            if rag_index is not None:
                hits = retrieve(
                    query=_mk_query(clause, obl),
                    index=rag_index,
                    top_k=cfg.top_k,
                    filters={"jurisdiction": juris} if juris else None,
                )

                ranked: List[Tuple[RagChunk, float]] = []
                if cfg.rerank and hits:
                    ranked = _rerank_hits(hits, obl)
                else:
                    ranked = [(h, 0.0) for h in hits]

                if ranked:
                    top_overlap = float(max((s for _, s in ranked), default=0.0))

                for (h, s) in ranked[: cfg.max_citations_per_finding * 2]:
                    reg_cits.append({
                        "doc_id": h.doc_id,
                        "chunk_id": h.chunk_id,
                        "page": h.meta.get("page"),
                        "title": h.meta.get("title"),
                        "source": _fmt_source(h),
                        "score": float(s),
                        "excerpt": h.text[:900],
                    })

                reg_cits = _dedupe_citations(reg_cits)[: cfg.max_citations_per_finding]

                # Recompute top_overlap from the final citations to ensure it reflects what we actually kept.
                if reg_cits:
                    try:
                        top_overlap = float(max((c.get("score", 0.0) for c in reg_cits), default=top_overlap))
                    except Exception:
                        pass

            gap = (
                f"Potential gap vs obligation '{obl.get('title','')}' ({juris}). "
                f"Verify the clause includes explicit commitments matching: {obl.get('requirement','')}"
            )

            sev = _severity_from(clause, obl)
            grounding_score = float(top_overlap)
            gl = _grounding_level(grounding_score, cfg)

            # Confidence is a function of grounding quality + clause strength heuristics.
            confidence = 0.35
            if reg_cits and len(reg_cits) >= cfg.min_hits_for_grounded:
                # scale 0.50..0.80 based on overlap proxy
                confidence = 0.50 + min(0.30, grounding_score * 1.2)
            status = "DRAFT"
            if not reg_cits or len(reg_cits) < cfg.min_hits_for_grounded or gl == "NONE":
                status = "NEEDS_REVIEW"

            findings.append({
                "finding_id": f"F-{clause.get('clause_id','CL')}-{obl.get('obligation_id','OBL')}",
                "clause_id": clause.get("clause_id", "UNKNOWN"),
                "obligation_id": obl.get("obligation_id", "UNKNOWN"),
                "gap_statement": gap,
                "risk_category": "REGULATORY",
                "severity": sev,
                "confidence": float(confidence),
                "grounding_score": grounding_score,
                "grounding_level": gl,
                "contract_evidence": clause.get("evidence_spans", []) or [],
                "reg_citations": reg_cits,
                "status": status,
                "jurisdiction": juris,
                "tags": obl.get("tags", []),
            })

    return AgentResult(data={"findings": findings, "mode": cfg.mode}, warnings=warnings)
