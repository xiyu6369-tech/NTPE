from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class ActivationEvidence:
    ab_ready: bool
    ab_status: str
    canary_status: str
    canary_activated_records: int
    estimated_tokens_saved: int
    provider_calls_added: int
    target_chunk_completed: bool
    fallback_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "fallback_reasons", tuple(self.fallback_reasons))


@dataclass(frozen=True)
class ActivationPolicyRequest:
    profile: str = "literary"
    rollout_percent: int = 0
    explicitly_enabled: bool = False
    kill_switch: bool = False


@dataclass(frozen=True)
class ActivationPolicyDecision:
    version: str
    status: str
    ready: bool
    mode: str
    profile: str
    rollout_percent: int
    blockers: tuple[str, ...]
    limitations: tuple[str, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "blockers", tuple(self.blockers))
        object.__setattr__(self, "limitations", tuple(self.limitations))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "status": self.status,
            "ready": self.ready,
            "mode": self.mode,
            "profile": self.profile,
            "rollout_percent": self.rollout_percent,
            "blockers": list(self.blockers),
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
        }
