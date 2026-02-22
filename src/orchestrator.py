from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schemas import AnalysisResult, AuditEvent, ContractMeta, Evidence, Finding, Summary
from .feature_extractor import extract_features
from .scoring import compute_score

from .agents.extractor import run_extractor, ExtractorConfig
from .agents.obligation_mapper import run_obligation_mapper, ObligationMapperConfig
from .agents.auditor import run_auditor, AuditorConfig
from .agents.verifier import run_verifier, VerifierConfig
from .agents.reviewer import run_reviewer, ReviewerConfig

from .rag.indexer import load_index
from .rag.store import RagIndex


@dataclass
class OrchestratorConfig:
    enabled: bool = True
    jurisdictions: List[str] | None = None
    require_reg_citations: bool = True
    rag_index_path: str = "data/rag_index/reg_index.pkl"
    top_k: int = 8
    obligation_catalog_path: str = "src/regulation/obligations_catalog.json"


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _try_load_rag_index(path: str) -> Optional[RagIndex]:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return load_index(str(p))
    except Exception:
        return None


def run_agentic_contract_analysis(
    *,
    contract_text: str,
    title: str,
    source_type: str,
    config: Optional[OrchestratorConfig] = None,
) -> AnalysisResult:
    cfg = config or OrchestratorConfig()
    if cfg.jurisdictions is None:
        cfg.jurisdictions = ["EU", "AU"]

    now = _iso_utc_now()
    features = extract_features(contract_text)

    rag_index = _try_load_rag_index(cfg.rag_index_path)
    rag_available = rag_index is not None

    ext = run_extractor(contract_text, config=ExtractorConfig(mode="deterministic", max_clauses=40, min_chars=160))
    clauses = ext.data.get("clauses", [])

    obligations: List[Dict[str, Any]] = []
    for j in cfg.jurisdictions:
        om = run_obligation_mapper(jurisdiction=j, config=ObligationMapperConfig(mode="catalog", catalog_path=cfg.obligation_catalog_path))
        obligations.extend(om.data.get("obligations", []))

    aud = run_auditor(
        clauses=clauses,
        obligations=obligations,
        rag_index=rag_index,
        config=AuditorConfig(mode="tfidf_rag", top_k=cfg.top_k, min_hits_for_grounded=1, rerank=True, max_citations_per_finding=3),
    )
    findings_raw = aud.data.get("findings", [])

    ver = run_verifier(
        findings=findings_raw,
        config=VerifierConfig(require_contract_evidence=True, require_reg_citations=bool(cfg.require_reg_citations), min_confidence=0.25),
    )
    verified = ver.data.get("verified_findings", [])
    flags = ver.data.get("quality_flags", [])
    reason_counts = ver.data.get("reason_counts", {})
    needs_review = bool(ver.data.get("needs_human_review", False)) or (cfg.require_reg_citations and not rag_available)

    rev = run_reviewer(verified_findings=verified, config=ReviewerConfig(mode="deterministic"))
    scorecard = rev.data.get("risk_scorecard", {}) or {}

    mapped_findings: List[Finding] = []
    for f in verified:
        sev = str(f.get("severity", "Medium")).capitalize()
        if sev not in {"Low", "Medium", "High", "Critical"}:
            sev = "Medium"

        ev: List[Evidence] = []
        for e in f.get("contract_evidence", []) or []:
            ev.append(Evidence(clause_ref=str(e.get("clause_ref") or f.get("clause_id") or "Contract"), snippet=str(e.get("snippet") or "")[:500]))

        for c in f.get("reg_citations", []) or []:
            excerpt = c.get("excerpt") or c.get("text") or ""
            ev.append(Evidence(clause_ref=str(c.get("doc_id", "Regulation")), snippet=f"p.{c.get('page','?')}: " + str(excerpt)[:450]))

        reasons = f.get("quality_reasons") or []
        rec = "Build/refresh RAG index and rerun to ground citations."
        if f.get("status") == "VERIFIED":
            rec = "Verified with available evidence. Consider legal review before finalizing."
        if reasons:
            rec += " Reasons: " + ", ".join(reasons)

        mapped_findings.append(
            Finding(
                finding_id=str(f.get("finding_id", "F-UNKNOWN")),
                category="Regulatory",
                risk_statement=str(f.get("gap_statement", "Regulatory gap identified.")),
                severity=sev,  # type: ignore
                confidence=float(f.get("confidence", 0.5)),
                evidence=ev if ev else [Evidence(clause_ref="N/A", snippet="No evidence captured.")],
                recommendation=rec,
                proposed_redline=None,
            )
        )

    score, breakdown = compute_score(mapped_findings)

    # --- Single source of truth for "what the user sees" ---
    # Align the executive scorecard + headline summary to the same score/risk-level so the UI never contradicts itself.
    verified_count = sum(1 for f in verified if (f.get("status") == "VERIFIED"))
    needs_review_count = sum(1 for f in verified if (f.get("status") == "NEEDS_REVIEW"))

    # Normalize scorecard keys so any UI renderer can find them
    scorecard = dict(scorecard) if isinstance(scorecard, dict) else {}
    scorecard["risk_level"] = breakdown.risk_level
    scorecard["score"] = float(score)
    scorecard["overall_score"] = float(score)
    scorecard["overall_score_0_100"] = float(score)
    scorecard["verified_count"] = int(verified_count)
    scorecard["needs_review_count"] = int(needs_review_count)
    scorecard["reason_counts"] = reason_counts

    # Make the "why needs review" visible even if UI doesn't have a dedicated widget
    if needs_review_count:
        breakdown_lines = []
        if reason_counts.get("MISSING_REG_CITATIONS"):
            breakdown_lines.append(f"Missing regulation citations: {reason_counts.get('MISSING_REG_CITATIONS')}")
        if reason_counts.get("MISSING_CONTRACT_EVIDENCE"):
            breakdown_lines.append(f"Missing contract evidence: {reason_counts.get('MISSING_CONTRACT_EVIDENCE')}")
        if reason_counts.get("LOW_CONFIDENCE"):
            breakdown_lines.append(f"Low confidence: {reason_counts.get('LOW_CONFIDENCE')}")
        if breakdown_lines:
            msg = "Needs review breakdown — " + "; ".join(breakdown_lines)
            nxt = scorecard.get("recommended_next_steps") or []
            if isinstance(nxt, list):
                scorecard["recommended_next_steps"] = [msg] + nxt
            else:
                scorecard["recommended_next_steps"] = [msg]

    top_risks = [{"category": f.category, "title": f.risk_statement[:60]} for f in mapped_findings[:3]]
    summary = Summary(overall_risk_score=int(round(score)), risk_level=breakdown.risk_level, top_risks=top_risks)

    audit_events = [
        AuditEvent(ts=now, event="UPLOAD_RECEIVED", details={"source_type": source_type, "title": title}),
        AuditEvent(
            ts=now,
            event="AGENTIC_RUN",
            details={
                "jurisdictions": cfg.jurisdictions,
                "rag_available": rag_available,
                "rag_index_path": cfg.rag_index_path,
                "needs_human_review": needs_review,
                "quality_flags": flags,
                "scorecard": scorecard,
                "modes": {"extractor": "deterministic", "obligation_mapper": "catalog", "auditor": "tfidf_rag+rerank", "reviewer": "deterministic"},
            },
        ),
    ]

    return AnalysisResult(
        run_id="agentic-" + now.replace(":", "").replace("-", ""),
        contract=ContractMeta(title=title, source_type=source_type, text_length=len(contract_text)),
        summary=summary,
        findings=mapped_findings,
        features=features,
        scoring=breakdown,
        audit=audit_events,
    )
