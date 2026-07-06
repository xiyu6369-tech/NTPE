from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class DeploymentProfile:
    """Immutable enterprise deployment profile descriptor.

    Stage-18.3 is an additive profile layer. It does not mutate any frozen runtime
    contracts; it only describes deployment intent for later enterprise rollout steps.
    """

    name: str
    target: str
    environment: str
    mode: str = "additive"
    enabled_capabilities: List[str] = field(default_factory=list)
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    compatibility_contract: List[str] = field(default_factory=lambda: [
        "Foundation v1.0 remains frozen and untouched.",
        "NTPE 1.1 LTS frozen contracts remain compatible.",
        "Stage-17 production platform freeze remains valid.",
        "Stage-18.2 configuration center remains the canonical config source.",
    ])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "target": self.target,
            "environment": self.environment,
            "mode": self.mode,
            "enabled_capabilities": list(self.enabled_capabilities),
            "config_overrides": dict(self.config_overrides),
            "compatibility_contract": list(self.compatibility_contract),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "DeploymentProfile":
        return cls(
            name=str(payload.get("name", "default")),
            target=str(payload.get("target", "local-workstation")),
            environment=str(payload.get("environment", "development")),
            mode=str(payload.get("mode", "additive")),
            enabled_capabilities=list(payload.get("enabled_capabilities", [])),
            config_overrides=dict(payload.get("config_overrides", {})),
            compatibility_contract=list(payload.get("compatibility_contract", cls.__dataclass_fields__["compatibility_contract"].default_factory())),
        )
