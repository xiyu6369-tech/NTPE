from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class StrategySelectionEvidence:
    policy_ready: bool
    policy_status: str
    policy_mode: str
    policy_profile: str
    rollout_percent: int
    budget_ready: bool
    budget_status: str
    budget_profile: str
    effective_context_tokens: int
    profile_cap_tokens: int
    hard_limit_tokens: int


@dataclass(frozen=True)
class StrategySelectionRequest:
    profile: str
    explicitly_enabled: bool = False
    kill_switch: bool = False


@dataclass(frozen=True)
class StrategySelectionDecision:
    version: str
    status: str
    ready: bool
    strategy: str
    profile: str
    rollout_percent: int
    effective_context_tokens: int
    blockers: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
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
            "strategy": self.strategy,
            "profile": self.profile,
            "rollout_percent": self.rollout_percent,
            "effective_context_tokens": self.effective_context_tokens,
            "blockers": list(self.blockers),
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
        }
