from __future__ import annotations

from datetime import datetime, timezone
import random, string

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


def _run_id() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    return f"{ts}_{suffix}"


def analyze_contract(contract_text: str, title: str, source_type: str) -> AnalysisResult:
    """
    Adapter boundary.
    Later you replace internals with your actual prompt pipeline / RAG
    without changing Streamlit UI code.

    Output always includes:
    - structured findings
    - extracted features (DS handshake)
    - scoring breakdown (explainability)
    """
    rid = _run_id()
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # 1) Extract features first (this mirrors real pipelines: parse -> features -> model -> outputs)
    features = extract_features(contract_text)

    # 2) Demo findings (rule-based-ish, consistent with features)
    # In real implementation: the model produces these findings.
    findings = []

    if any(f.name == "has_uncapped_liability" and f.value for f in features.features) or \
       any(f.name == "has_consequential_damages" and f.value for f in features.features):
        findings.append(
            Finding(
                finding_id="R-001",
                category="Liability",
                risk_statement="Liability appears uncapped and/or includes consequential damages.",
                severity="High",
                confidence=0.78,
                evidence=[Evidence(clause_ref="Section 9.2", snippet="...liable for all damages including consequential...")],
                recommendation="Cap liability to 12 months of fees and exclude consequential damages.",
                proposed_redline="Total liability shall not exceed fees paid in the preceding 12 months..."
            )
        )

    if any(f.name == "has_termination_for_convenience" and f.value for f in features.features) and \
       not any(f.name == "has_cure_period" and f.value for f in features.features):
        findings.append(
            Finding(
                finding_id="R-002",
                category="Termination",
                risk_statement="Termination for convenience may allow exit without cure period.",
                severity="Medium",
                confidence=0.70,
                evidence=[Evidence(clause_ref="Section 12.1", snippet="Either party may terminate for convenience upon notice...")],
                recommendation="Add a cure period and limit termination for convenience."
            )
        )

    # If nothing matched, still return a clean result (important for robustness)
    if not findings:
        findings.append(
            Finding(
                finding_id="R-000",
                category="General",
                risk_statement="No high-signal risk clauses detected by the demo rules.",
                severity="Low",
                confidence=0.60,
                evidence=[Evidence(clause_ref="N/A", snippet="No matched patterns in provided text.")],
                recommendation="Run with a larger contract sample or connect to the full model pipeline."
            )
        )

    # 3) Scoring with explainability
    score, breakdown = compute_score(findings)

    # 4) Summary derived from scoring
    top_risks = [{"category": f.category, "title": f.risk_statement[:60]} for f in findings[:2]]
    summary = Summary(
        overall_risk_score=score,
        risk_level=breakdown.risk_level,
        top_risks=top_risks,
    )

    return AnalysisResult(
        run_id=rid,
        contract=ContractMeta(title=title, source_type=source_type, text_length=len(contract_text)),
        summary=summary,
        findings=findings,
        features=features,
        scoring=breakdown,
        audit=[
            AuditEvent(ts=now, event="UPLOAD_RECEIVED", details={"source_type": source_type}),
            AuditEvent(ts=now, event="FEATURES_EXTRACTED", details={"feature_count": len(features.features)}),
            AuditEvent(ts=now, event="SCORING_COMPLETED", details={"score": score, "level": breakdown.risk_level}),
            AuditEvent(ts=now, event="ANALYSIS_COMPLETED"),
        ],
    )