from src.model_adapter import analyze_contract


def test_model_adapter_returns_contract_fields():
    res = analyze_contract("terminate for convenience", title="T", source_type="paste")
    d = res.model_dump()

    assert "run_id" in d
    assert "summary" in d
    assert "findings" in d
    assert "features" in d
    assert "scoring" in d

    assert isinstance(d["findings"], list)
    assert isinstance(d["features"]["features"], list)
    assert isinstance(d["scoring"]["items"], list)