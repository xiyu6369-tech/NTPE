from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

PHASES = frozenset({"generation", "local_repair", "quality_validation", "adaptive_retry"})
CATEGORIES = frozenset({"fidelity", "completeness", "hallucination", "terminology", "narrative", "naturalness", "formatting", "repetition", "chronology", "characterization"})


@dataclass(frozen=True)
class DisciplineRule:
    code: str
    category: str
    title: str
    instruction: str
    severity: str = "high"
    phase: str = "generation"
    enabled: bool = True
    retry_relevant: bool = False
    locally_repairable: bool = False
    evidence_required: bool = False
    profiles: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        code = self.code.strip().upper()
        if not code:
            raise ValueError("discipline rule code must not be empty")
        if self.phase not in PHASES:
            raise ValueError(f"unsupported discipline phase: {self.phase}")
        if self.category not in CATEGORIES:
            raise ValueError(f"unsupported discipline category: {self.category}")
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "profiles", tuple(self.profiles))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "category": self.category, "title": self.title, "instruction": self.instruction, "severity": self.severity, "phase": self.phase, "enabled": self.enabled, "retry_relevant": self.retry_relevant, "locally_repairable": self.locally_repairable, "evidence_required": self.evidence_required, "profiles": list(self.profiles), "metadata": dict(self.metadata)}
