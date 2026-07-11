from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class ShadowAuditRecord:
    version: str
    package_id: str
    mode: str
    payload_hash_before: str
    payload_hash_after: str
    payload_equivalent: bool
    provider_calls_added: int
    metrics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "package_id": self.package_id,
            "mode": self.mode,
            "payload_hash_before": self.payload_hash_before,
            "payload_hash_after": self.payload_hash_after,
            "payload_equivalent": self.payload_equivalent,
            "provider_calls_added": self.provider_calls_added,
            "metrics": dict(self.metrics),
        }
