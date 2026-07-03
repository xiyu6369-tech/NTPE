"""Package metadata model for NTPE Stage-14.1."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass(frozen=True)
class PackageMetadata:
    """Immutable build metadata used by packaging and release tasks."""

    name: str = "ntpe"
    version: str = "1.0.0-beta"
    stage: str = "Stage-14.1"
    profile: str = "beta"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    components: List[str] = field(default_factory=lambda: [
        "foundation",
        "cli",
        "sdk",
        "integration",
        "workflow",
        "platform_services",
        "runtime_api",
        "external_api",
        "web_ui",
        "packaging",
    ])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "stage": self.stage,
            "profile": self.profile,
            "created_at": self.created_at,
            "components": list(self.components),
        }
