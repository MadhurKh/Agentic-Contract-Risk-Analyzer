from src.evaluation_stub import load_cases, run_evaluation

def test_eval_harness_loads_and_runs():
    cases = load_cases("sample_data/eval_cases.json")
    metrics = run_evaluation(cases)
    assert "risk_level_accuracy" in metrics
    assert metrics["n"] > 0