from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import re

from ._common import AgentResult


@dataclass
class ExtractorConfig:
    """Configuration for clause extraction."""
    mode: str = "deterministic"  # deterministic | llm | hybrid
    max_clauses: int = 30
    min_chars: int = 200


_SECTION_RE = re.compile(r"^(\s*(?:section\s+)?\d+(?:\.\d+)*\s*[:\-\)]\s+.+)$", re.IGNORECASE)
_HEADING_RE = re.compile(r"^\s*[A-Z][A-Z\s\-]{4,}$")
_BULLET_RE = re.compile(r"^\s*(?:\-|\*|\u2022)\s+")


def _guess_clause_type(text: str) -> str:
    t = (text or "").lower()
    # Order matters: pick most specific first
    rules = [
        ("DATA_RETENTION", ["retention", "retain", "deletion", "delete", "purge"]),
        ("PRIVACY_DATA", ["personal data", "pii", "gdpr", "privacy", "data protection"]),
        ("SECURITY", ["security", "encryption", "iso 27001", "access control", "incident", "breach"]),
        ("AUDIT_RIGHTS", ["audit", "inspection", "right to audit", "assurance"]),
        ("SUBPROCESSORS", ["subprocessor", "sub-contract", "third party", "affiliate", "vendors"]),
        ("LIABILITY", ["liability", "indemn", "limitation", "cap", "damages"]),
        ("GOVERNANCE", ["governance", "policy", "controls", "compliance", "monitoring"]),
        ("TRANSPARENCY", ["transparency", "disclosure", "explain", "notice"]),
        ("HUMAN_OVERSIGHT", ["human oversight", "human review", "manual review", "escalation"]),
        ("LOGGING", ["logging", "logs", "trace", "audit trail"]),
        ("MODEL_RISK", ["model", "ai", "machine learning", "algorithm", "automated decision"]),
        ("IP", ["intellectual property", "ip", "ownership", "license"]),
        ("TERMINATION", ["termination", "terminate", "exit", "wind down"]),
    ]
    for label, kws in rules:
        if any(k in t for k in kws):
            return label
    return "GENERAL"


def _split_into_sections(text: str) -> List[Tuple[str, str]]:
    """Returns list of (heading, body)."""
    lines = (text or "").splitlines()
    sections: List[Tuple[str, List[str]]] = []
    cur_h = "Preamble"
    cur_body: List[str] = []

    def flush():
        nonlocal cur_h, cur_body
        body = "\n".join(cur_body).strip()
        if body:
            sections.append((cur_h.strip()[:120], body))
        cur_body = []

    for line in lines:
        raw = line.rstrip()
        if not raw.strip():
            cur_body.append(raw)
            continue

        is_section = bool(_SECTION_RE.match(raw)) or bool(_HEADING_RE.match(raw))
        if is_section and len(cur_body) >= 3:
            flush()
            cur_h = raw.strip()
            continue

        cur_body.append(raw)

    flush()
    return [(h, b) for h, b in sections if b.strip()]


def run_extractor(contract_text: str, *, config: Optional[ExtractorConfig] = None) -> AgentResult:
    """
    Agent 1 — Extractor (deterministic MVP)

    - Splits contract into sections using simple heading heuristics
    - Creates clause objects with evidence spans/snippets
    - Assigns a coarse clause_type via keyword rules
    """
    cfg = config or ExtractorConfig()

    text = contract_text or ""
    if not text.strip():
        return AgentResult(data={"clauses": [], "extractor_mode": cfg.mode}, warnings=["Empty contract text."])

    sections = _split_into_sections(text)

    clauses: List[Dict[str, Any]] = []
    offset = 0
    for i, (heading, body) in enumerate(sections[: cfg.max_clauses], start=1):
        clause_text = f"{heading}\n{body}".strip()
        if len(clause_text) < cfg.min_chars and i != 1:
            continue

        # Locate clause text in full string (best-effort)
        idx = text.find(body, offset)
        if idx == -1:
            idx = text.find(body)
        start = max(0, idx if idx != -1 else offset)
        end = min(len(text), start + min(len(clause_text), 1200))
        snippet = text[start:end]

        clauses.append(
            {
                "clause_id": f"CL-{i:04d}",
                "clause_type": _guess_clause_type(clause_text),
                "clause_text": clause_text,
                "evidence_spans": [{"start": start, "end": end, "snippet": snippet}],
                "confidence": 0.70,
            }
        )
        offset = end

    if not clauses:
        # fallback: whole text
        clauses = [
            {
                "clause_id": "CL-0001",
                "clause_type": "FULL_TEXT",
                "clause_text": text,
                "evidence_spans": [{"start": 0, "end": min(len(text), 1200), "snippet": text[:1200]}],
                "confidence": 0.55,
            }
        ]

    return AgentResult(
        data={"clauses": clauses, "extractor_mode": cfg.mode},
        warnings=["Extractor uses heuristic section splitting (deterministic MVP)."],
    )
