from src.model_adapter import analyze_contract

def test_all_findings_have_evidence():
    text = "Vendor is liable for all damages including consequential. Liability is uncapped."
    result = analyze_contract(text, title="Test", source_type="paste").model_dump()
    findings = result.get("findings", [])
    assert len(findings) > 0

    for f in findings:
        ev = f.get("evidence", [])
        assert isinstance(ev, list)
        assert len(ev) >= 1
        assert ev[0].get("snippet")