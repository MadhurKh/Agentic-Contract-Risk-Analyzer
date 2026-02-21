from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ._common import AgentResult


@dataclass
class ExtractorConfig:
    mode: str = "deterministic"
    max_clauses: int = 40
    # Lowered to avoid dropping legitimate short clauses (common in contracts)
    min_chars: int = 80


_HEADING_RE = re.compile(r"^(\s*)([A-Z][A-Z\s\-\&]{6,})(:)?\s*$")
_CLAUSE_NUM_RE = re.compile(r"^(\s*)(\d+(?:\.\d+){0,4})(\)|\.|\s)\s+(.*)$")

_TYPE_RULES: List[Tuple[str, List[str]]] = [
    ("SECURITY", ["security", "cyber", "encryption", "encrypt", "vulnerability", "patch", "mfa", "multi-factor", "access control", "secure", "penetration", "soc 2", "iso 27001"]),
    ("PRIVACY_DATA", ["personal data", "pii", "privacy", "gdpr", "data subject", "controller", "processor", "anonym", "pseudonym", "confidential information"]),
    ("DATA_PROCESSING", ["process data", "data processing", "sub-processor", "subprocessor", "processing activities", "data transfer", "cross-border", "third country"]),
    ("NOTICE", ["notice", "notify", "disclose", "transparency", "inform", "user notice"]),
    ("TRANSPARENCY", ["transparency", "explain", "explanation", "ai system", "automated decision", "model output", "disclose ai"]),
    ("LOGGING", ["log", "logging", "audit log", "trace", "traceability", "record-keeping", "record keeping"]),
    ("AUDIT_RIGHTS", ["audit", "inspection", "access to records", "right to audit", "verify compliance"]),
    ("HUMAN_OVERSIGHT", ["human oversight", "human in the loop", "manual review", "override", "escalation", "supervision"]),
    ("INCIDENT_RESPONSE", ["incident", "breach", "notifiable", "ndb", "notify authority", "security incident", "response plan"]),
    ("DATA_RETENTION", ["retention", "retain", "deletion", "delete", "destroy", "storage limitation", "archiv"]),
    ("ACCESS_CONTROL", ["access control", "least privilege", "role based", "rbac", "authentication", "authorization"]),
    ("BACKUP_RECOVERY", ["backup", "disaster recovery", "business continuity", "restore", "rto", "rpo"]),
    ("MODEL_RISK", ["model risk", "bias", "fairness", "drift", "monitoring", "robustness", "accuracy", "testing", "validation"]),
    ("GOVERNANCE", ["governance", "policy", "compliance", "controls", "risk management", "responsibility", "accountability"]),
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _segment_contract(text: str) -> List[Dict[str, Any]]:
    lines = (text or "").splitlines()
    blocks: List[Dict[str, Any]] = []

    current_heading: Optional[str] = None
    current_num: Optional[str] = None
    buf: List[str] = []

    def flush():
        nonlocal buf, current_num, current_heading
        if not buf:
            return
        clause_text = "\n".join(buf).strip()
        if clause_text:
            blocks.append({"heading": current_heading, "clause_num": current_num, "text": clause_text})
        buf = []

    for ln in lines:
        if not ln.strip():
            if buf:
                buf.append("")
            continue

        h = _HEADING_RE.match(ln)
        if h:
            flush()
            current_heading = h.group(2).strip()
            current_num = None
            continue

        m = _CLAUSE_NUM_RE.match(ln)
        if m:
            flush()
            current_num = m.group(2)
            buf.append(m.group(4))
            continue

        buf.append(ln)

    flush()
    return blocks


def _classify_clause(text: str, heading: Optional[str] = None) -> Tuple[str, float, float]:
    t = _normalize(text)
    h = _normalize(heading or "")
    combined = (h + " " + t).strip()

    best_type = "GOVERNANCE"
    best_score = 0.0

    for clause_type, keywords in _TYPE_RULES:
        score = 0
        for kw in keywords:
            if kw in combined:
                score += 1
        if score > best_score:
            best_score = float(score)
            best_type = clause_type

    if best_score >= 4:
        conf = 0.85
    elif best_score == 3:
        conf = 0.75
    elif best_score == 2:
        conf = 0.65
    elif best_score == 1:
        conf = 0.55
    else:
        conf = 0.40

    return best_type, conf, best_score


def _evidence_span(clause_id: str, clause_text: str) -> Dict[str, str]:
    snippet = _normalize(clause_text)[:220]
    return {"clause_ref": clause_id, "snippet": snippet}


def run_extractor(contract_text: str, config: Optional[ExtractorConfig] = None) -> AgentResult:
    cfg = config or ExtractorConfig()

    blocks = _segment_contract(contract_text)
    clauses: List[Dict[str, Any]] = []

    for i, b in enumerate(blocks):
        text = (b.get("text") or "").strip()
        heading = b.get("heading")
        clause_type, conf, score = _classify_clause(text, heading)

        # allow shorter clauses if we have strong classification signal
        if len(text) < cfg.min_chars and score < 2:
            continue

        clause_id = b.get("clause_num") or f"CL-{i+1:03d}"

        clauses.append(
            {
                "clause_id": clause_id,
                "section_heading": heading,
                "clause_type": clause_type,
                "clause_confidence": conf,
                "clause_text": text,
                "evidence_spans": [_evidence_span(clause_id, text)],
            }
        )

        if len(clauses) >= cfg.max_clauses:
            break

    warnings: List[str] = []
    if not clauses:
        warnings.append("No clauses extracted (contract may be too short or formatting not recognized).")

    return AgentResult(data={"clauses": clauses, "mode": cfg.mode}, warnings=warnings)
