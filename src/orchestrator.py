from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schemas import (
    AnalysisResult,
    AuditEvent,
    ContractMeta,
    Evidence,
    Finding,
    Summary,
)
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
    top_k: int = 5
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

    # 1) Extractor (deterministic MVP)
    ext = run_extractor(contract_text, config=ExtractorConfig(mode="deterministic", max_clauses=30, min_chars=200))
    clauses = ext.data.get("clauses", [])

    # 2) Obligation Mapper (catalog)
    obligations: List[Dict[str, Any]] = []
    for j in cfg.jurisdictions:
        om = run_obligation_mapper(
            jurisdiction=j,
            config=ObligationMapperConfig(mode="catalog", catalog_path=cfg.obligation_catalog_path),
        )
        obligations.extend(om.data.get("obligations", []))

    # 3) Auditor (TF-IDF RAG if index exists)
    aud = run_auditor(
        clauses=clauses,
        obligations=obligations,
        rag_index=rag_index,
        config=AuditorConfig(mode="tfidf_rag", top_k=cfg.top_k),
    )
    findings_raw = aud.data.get("findings", [])

    # 4) Verifier (citations required only if index exists; otherwise mark for review)
    require_cits = bool(cfg.require_reg_citations) and rag_available
    ver = run_verifier(
        findings=findings_raw,
        config=VerifierConfig(
            require_contract_evidence=True,
            require_reg_citations=require_cits,
            min_confidence=0.25,
        ),
    )
    verified = ver.data.get("verified_findings", [])
    flags = ver.data.get("quality_flags", [])
    needs_review = bool(ver.data.get("needs_human_review", False)) or (cfg.require_reg_citations and not rag_available)

    # 5) Reviewer (exec scorecard deterministic)
    rev = run_reviewer(verified_findings=verified, config=ReviewerConfig(mode="deterministic"))
    scorecard = rev.data.get("risk_scorecard", {})

    mapped_findings: List[Finding] = []
    for f in verified:
        sev = str(f.get("severity", "Medium")).capitalize()
        if sev not in {"Low", "Medium", "High", "Critical"}:
            sev = "Medium"

        ev: List[Evidence] = []

        for e in f.get("contract_evidence", []) or []:
            snippet = e.get("snippet") or ""
            clause_ref = e.get("clause_ref") or f.get("clause_id") or "Contract"
            ev.append(Evidence(clause_ref=str(clause_ref), snippet=str(snippet)[:500]))

        reg_cits = f.get("reg_citations", []) or []
        for c in reg_cits:
            ev.append(
                Evidence(
                    clause_ref=str(c.get("doc_id", "Regulation")),
                    snippet=f"p.{c.get('page','?')}: " + str(c.get("text", ""))[:450],
                )
            )

        status = f.get("status", "DRAFT")
        reasons = f.get("quality_reasons") or []
        rec = "Build/enable RAG citations and rerun to verify. "
        if status == "VERIFIED":
            rec = "Verified with available evidence. "
        if reasons:
            rec += f"Reasons: {', '.join(reasons)}"

        mapped_findings.append(
            Finding(
                finding_id=str(f.get("finding_id", "F-UNKNOWN")),
                category="Regulatory",
                risk_statement=str(f.get("gap_statement", "Regulatory gap identified.")),
                severity=sev,  # type: ignore
                confidence=float(f.get("confidence", 0.5)),
                evidence=ev if ev else [Evidence(clause_ref="N/A", snippet="No evidence captured.")],
                recommendation=rec.strip(),
                proposed_redline=None,
            )
        )

    if not mapped_findings:
        mapped_findings = [
            Finding(
                finding_id="A-000",
                category="Regulatory",
                risk_statement="No findings produced by agentic pipeline (unexpected).",
                severity="Low",
                confidence=0.5,
                evidence=[Evidence(clause_ref="N/A", snippet="No findings returned.")],
                recommendation="Check pipeline wiring and input data.",
            )
        ]

    score, breakdown = compute_score(mapped_findings)

    top_risks = [{"category": f.category, "title": f.risk_statement[:60]} for f in mapped_findings[:3]]
    summary = Summary(overall_risk_score=score, risk_level=breakdown.risk_level, top_risks=top_risks)

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
                "modes": {"extractor": "deterministic", "obligation_mapper": "catalog", "auditor": "tfidf_rag", "reviewer": "deterministic"},
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
