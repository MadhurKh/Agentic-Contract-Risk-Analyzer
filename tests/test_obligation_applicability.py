from src.agents.auditor import run_auditor
from src.agents.obligation_mapper import run_obligation_mapper


def test_obligation_applicability_filters_cross_product():
    clauses = [
        {"clause_id": "C1", "clause_type": "SECURITY", "clause_text": "Security controls and encryption...", "evidence_spans": [{"clause_ref": "C1", "snippet": "encryption"}]},
        {"clause_id": "C2", "clause_type": "TRANSPARENCY", "clause_text": "We will disclose AI usage to users...", "evidence_spans": [{"clause_ref": "C2", "snippet": "disclose"}]},
    ]

    eu_obls = run_obligation_mapper(jurisdiction="EU").data["obligations"]
    findings = run_auditor(clauses=clauses, obligations=eu_obls, rag_index=None).data["findings"]

    assert len(findings) > 0
    assert len(findings) < 10
