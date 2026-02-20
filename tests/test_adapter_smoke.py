from src.model_adapter import analyze_contract

def test_analyze_contract_smoke():
    result = analyze_contract("Test contract text", title="Test", source_type="paste")
    d = result.model_dump()
    assert "run_id" in d
    assert "summary" in d