from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class EnterpriseConfigSchema:
    """Minimal additive schema for enterprise configuration.

    The schema is intentionally conservative: it validates enterprise deployment
    metadata without changing legacy runtime configuration contracts.
    """

    version: str = "1.2"
    required_sections: List[str] = field(
        default_factory=lambda: [
            "enterprise",
            "runtime",
            "translation",
            "platform",
        ]
    )
    enterprise_required_keys: List[str] = field(
        default_factory=lambda: ["enabled", "environment", "profile", "config_version"]
    )

    def to_dict(self) -> Dict[str, object]:
        return {
            "version": self.version,
            "required_sections": list(self.required_sections),
            "enterprise_required_keys": list(self.enterprise_required_keys),
        }
