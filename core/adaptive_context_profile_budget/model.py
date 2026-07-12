from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class ProfileBudgetRequest:
    profile: str
    model_context_limit: int
    fixed_prompt_tokens: int
    source_tokens: int
    reserved_output_tokens: int
    requested_context_tokens: int | None = None


@dataclass(frozen=True)
class ProfileBudgetDecision:
    version: str
    status: str
    ready: bool
    profile: str
    profile_cap_tokens: int
    hard_limit_tokens: int
    requested_context_tokens: int
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
            "profile": self.profile,
            "profile_cap_tokens": self.profile_cap_tokens,
            "hard_limit_tokens": self.hard_limit_tokens,
            "requested_context_tokens": self.requested_context_tokens,
            "effective_context_tokens": self.effective_context_tokens,
            "blockers": list(self.blockers),
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
        }
