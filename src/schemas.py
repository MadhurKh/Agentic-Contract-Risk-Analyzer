from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Severity = Literal["Low", "Medium", "High", "Critical"]


class Evidence(BaseModel):
    clause_ref: str
    snippet: str


class Finding(BaseModel):
    finding_id: str
    category: str
    risk_statement: str
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[Evidence] = Field(default_factory=list)
    recommendation: str
    proposed_redline: Optional[str] = None


class ContractMeta(BaseModel):
    title: str
    source_type: Literal["paste", "upload"]
    text_length: int


class Summary(BaseModel):
    overall_risk_score: int = Field(ge=0, le=100)
    risk_level: Literal["Low", "Medium", "High", "Critical"]
    top_risks: List[Dict[str, str]] = Field(default_factory=list)


class AuditEvent(BaseModel):
    ts: str  # ISO8601 Z
    event: str
    details: Optional[Dict[str, Any]] = None


# ---- NEW: Features extracted (DS handshake) ----
class Feature(BaseModel):
    name: str
    value: Any
    dtype: Literal["bool", "int", "float", "str", "list", "dict"]


class FeatureSet(BaseModel):
    version: str = "1.0"
    features: List[Feature] = Field(default_factory=list)


# ---- NEW: Scoring transparency ----
class SeverityWeights(BaseModel):
    Low: int
    Medium: int
    High: int
    Critical: int


class ScoringBreakdownItem(BaseModel):
    finding_id: str
    severity: Severity
    weight: int
    confidence: float
    points: float


class ScoringBreakdown(BaseModel):
    method: str = "weighted_severity_sum_v1"
    weights: SeverityWeights
    total_points: float
    normalized_score_0_100: int
    risk_level: Literal["Low", "Medium", "High", "Critical"]
    items: List[ScoringBreakdownItem] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    run_id: str
    contract: ContractMeta
    summary: Summary
    findings: List[Finding] = Field(default_factory=list)
    audit: List[AuditEvent] = Field(default_factory=list)

    # NEW fields (safe additions)
    features: Optional[FeatureSet] = None
    scoring: Optional[ScoringBreakdown] = None