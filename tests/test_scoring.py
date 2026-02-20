from src.schemas import Evidence, Finding
from src.scoring import compute_score


def test_scoring_in_range():
    findings = [
        Finding(
            finding_id="R-1",
            category="Test",
            risk_statement="test",
            severity="High",
            confidence=1.0,
            evidence=[Evidence(clause_ref="X", snippet="Y")],
            recommendation="Z",
        )
    ]
    score, breakdown = compute_score(findings)
    assert 0 <= score <= 100
    assert breakdown.normalized_score_0_100 == score
    assert breakdown.items[0].finding_id == "R-1"