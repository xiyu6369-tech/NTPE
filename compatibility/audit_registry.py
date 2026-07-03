"""Compatibility audit registry."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict
from .audit_model import CompatibilityTarget, CompatibilityAuditResult

@dataclass
class CompatibilityAuditRegistry:
    targets: Dict[str, CompatibilityTarget] = field(default_factory=dict)

    @classmethod
    def default(cls) -> "CompatibilityAuditRegistry":
        audit = CompatibilityAuditResult.default()
        return cls({target.name: target for target in audit.targets})

    def register(self, target: CompatibilityTarget) -> None:
        self.targets[target.name] = target

    def require(self, name: str) -> CompatibilityTarget:
        if name not in self.targets:
            raise KeyError(f"Compatibility target not registered: {name}")
        return self.targets[name]

    def names(self) -> list[str]:
        return list(self.targets.keys())

    def validate(self) -> Dict[str, object]:
        return self.to_result().validate()

    def to_result(self) -> CompatibilityAuditResult:
        return CompatibilityAuditResult(list(self.targets.values()))
