from __future__ import annotations
from typing import Protocol
from .schemas import AnalysisResult


class ContractRiskModel(Protocol):
    """
    DS/ML team can implement this interface.
    UI/Engineering should only depend on this contract.
    """

    def analyze_contract(self, contract_text: str, title: str, source_type: str) -> AnalysisResult:
        ...