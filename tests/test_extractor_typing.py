from src.agents.extractor import run_extractor, ExtractorConfig


def test_extractor_detects_security_and_privacy_types():
    contract = """\
1. SECURITY
We will maintain appropriate security controls including encryption in transit and at rest, multi-factor authentication, patching, and access control.

2. PRIVACY
We will process personal data in accordance with GDPR and applicable privacy laws. We will provide notice and support data subject requests.
"""

    res = run_extractor(contract, config=ExtractorConfig(min_chars=1)).data["clauses"]
    assert len(res) >= 2
    types = {c["clause_type"] for c in res}
    assert "SECURITY" in types
    assert ("PRIVACY_DATA" in types) or ("DATA_PROCESSING" in types)
