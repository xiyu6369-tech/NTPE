# =====================================================
# NTPE 1.2 Professional
# Stage-17.8 Production Platform Freeze
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class ProductionPlatformFreezeManifest:
    """Immutable production platform freeze manifest.

    Stage-17.8 is a freeze layer. It records the public production platform boundary
    introduced through Stage-17.1 to Stage-17.7 without mutating any frozen modules.
    """

    stage: str = "Stage-17.8"
    name: str = "Production Platform Freeze"
    version: str = "NTPE 1.2 Professional"
    status: str = "frozen"
    frozen_foundations: List[str] = field(
        default_factory=lambda: [
            "NTPE 1.0 Stable",
            "NTPE 1.1 LTS Stable",
            "Stage-15 Translation Quality Engine",
            "Stage-16 Intelligence Layer",
        ]
    )
    platform_components: List[str] = field(
        default_factory=lambda: [
            "Stage-17.1 Translation Workflow Engine",
            "Stage-17.2 Job Scheduler",
            "Stage-17.3 Resource Optimizer",
            "Stage-17.4 Review Approval Layer",
            "Stage-17.5 Export Framework",
            "Stage-17.6 Monitoring Dashboard API",
            "Stage-17.7 Production Runtime Integration",
        ]
    )
    compatibility_contract: List[str] = field(
        default_factory=lambda: [
            "GitHub main remains the only development baseline.",
            "Freeze layer is additive only.",
            "Foundation v1.0 files are not modified.",
            "NTPE 1.1 LTS Frozen behavior is not modified.",
            "Stage-17 public workflow/runtime APIs remain backward compatible.",
            "Production runtime keeps optional component injection behavior.",
        ]
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "frozen_foundations": list(self.frozen_foundations),
            "platform_components": list(self.platform_components),
            "compatibility_contract": list(self.compatibility_contract),
        }
