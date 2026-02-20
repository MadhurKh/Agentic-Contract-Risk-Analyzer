from __future__ import annotations

from typing import List, Literal, Tuple

from .schemas import Finding, ScoringBreakdown, ScoringBreakdownItem, SeverityWeights


RiskLevel = Literal["Low", "Medium", "High", "Critical"]


DEFAULT_WEIGHTS = SeverityWeights(Low=10, Medium=20, High=35, Critical=50)


def _risk_level(score: int) -> RiskLevel:
    # Simple, explainable thresholds for a demo.
    if score >= 80:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"


def compute_score(findings: List[Finding], weights: SeverityWeights = DEFAULT_WEIGHTS) -> Tuple[int, ScoringBreakdown]:
    """
    Weighted severity sum with confidence.
    points_i = weight(severity_i) * confidence_i
    score = normalize(total_points to 0-100 with a conservative cap)

    This is intentionally transparent and easy to review with DS/Model Risk.
    """
    items: List[ScoringBreakdownItem] = []
    total_points = 0.0

    weight_map = {
        "Low": weights.Low,
        "Medium": weights.Medium,
        "High": weights.High,
        "Critical": weights.Critical,
    }

    for f in findings:
        w = weight_map[f.severity]
        pts = float(w) * float(f.confidence)
        total_points += pts
        items.append(
            ScoringBreakdownItem(
                finding_id=f.finding_id,
                severity=f.severity,
                weight=w,
                confidence=f.confidence,
                points=round(pts, 2),
            )
        )

    # Conservative normalization:
    # Assume "critical portfolio" corresponds to ~3 critical findings at confidence 1.0
    # => max_points ~ 3 * 50 = 150
    max_points = 150.0
    normalized = int(round(min(100.0, (total_points / max_points) * 100.0)))

    level = _risk_level(normalized)

    breakdown = ScoringBreakdown(
        weights=weights,
        total_points=round(total_points, 2),
        normalized_score_0_100=normalized,
        risk_level=level,
        items=items,
    )
    return normalized, breakdown