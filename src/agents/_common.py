from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AgentResult:
    """Generic agent result container for early scaffolding."""
    data: Dict[str, Any]
    warnings: List[str] | None = None
    errors: List[str] | None = None
