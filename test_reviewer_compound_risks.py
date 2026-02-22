from src.agents.reviewer import run_reviewer, ReviewerConfig


def test_reviewer_generates_compound_risks():
    findings = [
        {"finding_id":"F1","clause_id":"C1","severity":"HIGH","confidence":0.7,"status":"NEEDS_REVIEW","tags":["cybersecurity"],"reg_citations":[]},
        {"finding_id":"F2","clause_id":"C2","severity":"MEDIUM","confidence":0.6,"status":"NEEDS_REVIEW","tags":["logging","traceability"],"reg_citations":[]},
    ]
    out = run_reviewer(verified_findings=findings, config=ReviewerConfig(top_risks=5))
    scorecard = out["risk_scorecard"]
    assert scorecard["overall_score"] >= 2.0
    assert len(scorecard.get("compound_risks", [])) >= 1
    assert "executive_summary" in scorecard and scorecard["executive_summary"]
