# =====================================================
# NTPE 1.2 Professional
# Stage-18.8 Enterprise Deployment Freeze Manifest
# =====================================================

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class EnterpriseDeploymentFreezeManifest:
    """Immutable Stage-18 freeze contract.

    The manifest records the enterprise deployment modules that are considered
    stable after Stage-18.8. It is intentionally descriptive and additive; it
    does not mutate deployment resources or frozen NTPE layers.
    """

    stage: str = "Stage-18.8"
    name: str = "Enterprise Deployment Freeze"
    version: str = "1.2-stage-18.8"
    status: str = "frozen"
    frozen_layers: List[str] = field(
        default_factory=lambda: [
            "Foundation v1.0",
            "NTPE 1.0 Stable",
            "NTPE 1.1 LTS Stable",
            "Stage-15 Quality Engine",
            "Stage-16 Intelligence Layer",
            "Stage-17 Production Platform",
            "Stage-18 Enterprise Deployment",
        ]
    )
    frozen_modules: List[str] = field(
        default_factory=lambda: [
            "core.enterprise.deployment_foundation",
            "core.enterprise.config_center",
            "core.enterprise.deployment_profiles",
            "core.enterprise.deployment_runtime",
            "core.enterprise.deployment_orchestrator",
            "core.enterprise.deployment_validation",
            "core.enterprise.deployment_freeze",
        ]
    )
    compatibility_rules: Dict[str, bool] = field(
        default_factory=lambda: {
            "additive_updates_only": True,
            "foundation_v1_locked": True,
            "lts_1_1_locked": True,
            "stage17_platform_locked": True,
            "no_destructive_actions": True,
            "backward_compatible": True,
        }
    )

    @property
    def manifest_hash(self) -> str:
        source = "|".join(
            [
                self.stage,
                self.name,
                self.version,
                self.status,
                *self.frozen_layers,
                *self.frozen_modules,
                *[f"{k}:{v}" for k, v in sorted(self.compatibility_rules.items())],
            ]
        )
        return hashlib.sha256(source.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "manifest_hash": self.manifest_hash,
            "frozen_layers": list(self.frozen_layers),
            "frozen_modules": list(self.frozen_modules),
            "compatibility_rules": dict(self.compatibility_rules),
        }
