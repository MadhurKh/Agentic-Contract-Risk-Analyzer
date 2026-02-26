from __future__ import annotations

from typing import List, Literal, Tuple

from .schemas import Finding, ScoringBreakdown, ScoringBreakdownItem, SeverityWeights


RiskLevel = Literal["Low", "Medium", "High", "Critical"]


DEFAULT_WEIGHTS = SeverityWeights(Low=10, Medium=20, High=35, Critical=50)

# Cap confidence contribution used for scoring to avoid score inflation when grounding heuristics improve.
# Confidence in findings can increase when better citations/overlap are found; the *risk* score should remain
# stable and reflect inherent exposure rather than citation-quality tuning.
CONFIDENCE_CAP_FOR_SCORING = 0.75


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
    Demo-friendly scoring that avoids saturating at 100 when there are many findings.

    1) points_i = weight(severity_i) * confidence_i
    2) focus on the worst exposures: take TOP_K findings by points (default 10)
    3) score = normalize(avg(points_top_k)) to 0–100, anchored to "High severity" weight.

    Rationale:
    - A sum-based normalization will almost always hit 100 when there are many findings.
    - A top-k average keeps the score sensitive to severity while staying stable across different finding counts.
    """
    items: List[ScoringBreakdownItem] = []
    total_points = 0.0

    weight_map = {
        "Low": weights.Low,
        "Medium": weights.Medium,
        "High": weights.High,
        "Critical": weights.Critical,
    }

    points_list = []
    for f in findings:
        w = weight_map[f.severity]
        effective_conf = float(f.confidence)
        if effective_conf > CONFIDENCE_CAP_FOR_SCORING:
            effective_conf = CONFIDENCE_CAP_FOR_SCORING
        pts = float(w) * float(effective_conf)
        total_points += pts
        points_list.append((f.finding_id, f.severity, w, effective_conf, pts))
        items.append(
            ScoringBreakdownItem(
                finding_id=f.finding_id,
                severity=f.severity,
                weight=w,
                confidence=effective_conf,
                points=round(pts, 2),
            )
        )

    # Worst-exposure focus
    if points_list:
        points_list.sort(key=lambda x: x[4], reverse=True)
        top_k = min(10, len(points_list))
        top_points = [p[4] for p in points_list[:top_k]]
        avg_top = sum(top_points) / float(top_k)
    else:
        top_k = 0
        avg_top = 0.0

    # Normalize against "High severity" anchor so Medium-high risks don't appear artificially low.
    anchor = float(weights.High) if float(weights.High) > 0 else 35.0
    normalized = int(round(min(100.0, (avg_top / anchor) * 100.0)))

    level = _risk_level(normalized)

    breakdown = ScoringBreakdown(
        method="weighted_severity_topk_avg_v2",
        weights=weights,
        total_points=round(total_points, 2),
        normalized_score_0_100=normalized,
        risk_level=level,
        items=items,
    )
    return normalized, breakdown
