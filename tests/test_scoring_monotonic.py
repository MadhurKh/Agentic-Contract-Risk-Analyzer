from src.schemas import Finding, Evidence
from src.scoring import compute_score

def test_high_severity_scores_higher_than_low():
    low = [
        Finding(
            finding_id="T-LOW",
            category="General",
            risk_statement="Low risk",
            severity="Low",
            confidence=1.0,
            evidence=[Evidence(clause_ref="X", snippet="...")],
            recommendation="N/A",
        )
    ]

    high = [
        Finding(
            finding_id="T-HIGH",
            category="Liability",
            risk_statement="High risk",
            severity="High",
            confidence=1.0,
            evidence=[Evidence(clause_ref="Y", snippet="...")],
            recommendation="N/A",
        )
    ]

    s_low, _ = compute_score(low)
    s_high, _ = compute_score(high)

    assert s_high > s_low