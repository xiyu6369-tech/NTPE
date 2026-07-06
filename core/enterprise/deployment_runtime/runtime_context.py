from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class EnterpriseRuntimeContext:
    """Resolved enterprise runtime context for additive deployment execution.

    This context carries deployment metadata only. It does not mutate frozen
    Foundation v1.0, NTPE 1.1 LTS, or translation runtime behavior.
    """

    profile: str
    environment: str
    target: str
    root: str
    capabilities: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)

    @property
    def root_path(self) -> Path:
        return Path(self.root).resolve()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile": self.profile,
            "environment": self.environment,
            "target": self.target,
            "root": str(self.root_path),
            "capabilities": list(self.capabilities),
            "config": dict(self.config),
        }

    @classmethod
    def from_config(cls, config: Dict[str, Any], root: str | Path = ".") -> "EnterpriseRuntimeContext":
        enterprise = dict(config.get("enterprise", {}))
        return cls(
            profile=str(enterprise.get("deployment_profile", enterprise.get("profile", "local-workstation"))),
            environment=str(enterprise.get("environment", "development")),
            target=str(enterprise.get("deployment_target", "local-workstation")),
            root=str(Path(root).resolve()),
            capabilities=list(enterprise.get("capabilities", [])),
            config=dict(config),
        )
