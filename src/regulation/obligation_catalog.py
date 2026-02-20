from __future__ import annotations

from typing import Dict, List


def starter_obligations(jurisdiction: str) -> List[Dict]:
    """Starter obligations used by Obligation Mapper in stub mode."""
    j = jurisdiction.upper()
    return [
        {
            "obligation_id": f"{j}-OBL-001",
            "jurisdiction": j,
            "title": "Transparency & Disclosure",
            "requirement": "Provide appropriate transparency, disclosures, and documentation where required.",
            "applies_if": "AI/ML systems or automated decisioning is used in service delivery.",
            "severity_weight": 1.0,
        },
        {
            "obligation_id": f"{j}-OBL-002",
            "jurisdiction": j,
            "title": "Risk Management",
            "requirement": "Maintain a documented risk management process for AI-related risks.",
            "applies_if": "Contract involves AI model development, deployment, or monitoring.",
            "severity_weight": 1.2,
        },
    ]
