from src.feature_extractor import extract_features


def test_extract_features_has_text_length():
    fs = extract_features("hello world")
    d = {f.name: f.value for f in fs.features}
    assert "text_length" in d
    assert d["text_length"] == 11


def test_extract_features_detects_flags():
    text = "This includes consequential damages and unlimited liability."
    fs = extract_features(text)
    d = {f.name: f.value for f in fs.features}
    assert d["has_consequential_damages"] is True
    assert d["has_uncapped_liability"] is True