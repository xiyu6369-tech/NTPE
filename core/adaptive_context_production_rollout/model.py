from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class ProductionEvidence:
    policy_version: str
    policy_ready: bool
    policy_status: str
    policy_mode: str
    policy_profile: str
    policy_rollout_percent: int
    budget_version: str
    budget_ready: bool
    budget_status: str
    budget_profile: str
    effective_context_tokens: int
    strategy_version: str
    strategy_ready: bool
    strategy_status: str
    strategy: str
    strategy_profile: str
    strategy_rollout_percent: int
    strategy_context_tokens: int
    evidence_fresh: bool = True
    evidence_integrity: bool = True
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class RolloutConfig:
    enabled: bool = False
    rollout_percent: int = 0
    profile: str = "literary"
    policy_version: str = "7.0.0-stage08.4"
    kill_switch: bool = False
    validation_mode: str = "assembly-only"
    target_chunk: int | None = None


@dataclass(frozen=True)
class SamplingDecision:
    bucket: int
    rollout_percent: int
    policy_version: str
    sampled: bool
    key_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "rollout_bucket": self.bucket,
            "rollout_percent": self.rollout_percent,
            "policy_version": self.policy_version,
            "sampled": self.sampled,
            "sampling_key_sha256": self.key_sha256,
        }


@dataclass(frozen=True)
class RolloutRecord:
    version: str
    package_id_sha256: str
    source_hash_sha256: str
    chunk_index: int
    profile: str
    decision: str
    activated: bool
    fallback_used: bool
    blockers: tuple[str, ...]
    rollout_bucket: int
    rollout_percent: int
    policy_version: str
    strategy_version: str
    baseline_context_tokens: int = 0
    ace_context_tokens: int = 0
    estimated_tokens_saved: int = 0
    payload_changed: bool = False
    provider_calls_added: int = 0
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "blockers", tuple(self.blockers))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "package_id_sha256": self.package_id_sha256,
            "source_hash_sha256": self.source_hash_sha256,
            "chunk_index": self.chunk_index,
            "profile": self.profile,
            "decision": self.decision,
            "activated": self.activated,
            "fallback_used": self.fallback_used,
            "blockers": list(self.blockers),
            "rollout_bucket": self.rollout_bucket,
            "rollout_percent": self.rollout_percent,
            "policy_version": self.policy_version,
            "strategy_version": self.strategy_version,
            "baseline_context_tokens": self.baseline_context_tokens,
            "ace_context_tokens": self.ace_context_tokens,
            "estimated_tokens_saved": self.estimated_tokens_saved,
            "payload_changed": self.payload_changed,
            "provider_calls_added": self.provider_calls_added,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RollbackDecision:
    version: str
    rollback: bool
    mode: str
    reasons: tuple[str, ...]
    provider_limitation: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "rollback": self.rollback,
            "mode": self.mode,
            "reasons": list(self.reasons),
            "provider_limitation": self.provider_limitation,
            "content_redacted": True,
        }
