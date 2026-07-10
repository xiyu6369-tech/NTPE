from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class QualityIssue:
    code: str
    severity: str
    message: str
    repair_action: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QualityReport:
    accepted: bool
    score: int
    issues: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    normalized_text: str
    stage: str = "TE-v5.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
