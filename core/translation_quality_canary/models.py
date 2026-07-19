from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CanaryConfiguration:
    model: str
    timeout_seconds: int
    glossary_sha256: str
    profile: str
    corpus_sha256: str
    base_prompt_tokens: int = 512
    glossary_tokens: int = 24

    def to_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "timeout_seconds": self.timeout_seconds,
            "glossary_sha256": self.glossary_sha256,
            "profile": self.profile,
            "corpus_sha256": self.corpus_sha256,
            "base_prompt_tokens": self.base_prompt_tokens,
            "glossary_tokens": self.glossary_tokens,
        }


@dataclass(frozen=True)
class CanaryArmRecord:
    case_id: str
    arm: str
    source_sha256: str
    input_fingerprint: str
    configuration_fingerprint: str
    flags: Mapping[str, bool]
    prompt_sha256: str
    prompt_tokens: int
    character_selected: int
    context_selected: int
    scene_selected: int
    budget_usage_tokens: int
    integration_latency_microseconds: int
    provider_requests: int = 0
    network_requests: int = 0
    translation_executed: bool = False
    translation_sha256: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "arm": self.arm,
            "source_sha256": self.source_sha256,
            "input_fingerprint": self.input_fingerprint,
            "configuration_fingerprint": self.configuration_fingerprint,
            "flags": dict(self.flags),
            "prompt_sha256": self.prompt_sha256,
            "prompt_tokens": self.prompt_tokens,
            "character_selected": self.character_selected,
            "context_selected": self.context_selected,
            "scene_selected": self.scene_selected,
            "budget_usage_tokens": self.budget_usage_tokens,
            "integration_latency_microseconds": self.integration_latency_microseconds,
            "provider_requests": self.provider_requests,
            "network_requests": self.network_requests,
            "translation_executed": self.translation_executed,
            "translation_sha256": self.translation_sha256,
        }


@dataclass(frozen=True)
class CanaryPairRecord:
    case_id: str
    categories: tuple[str, ...]
    baseline: CanaryArmRecord
    candidate: CanaryArmRecord
    parity_verified: bool
    only_feature_flags_differ: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "categories": list(self.categories),
            "baseline": self.baseline.to_dict(),
            "candidate": self.candidate.to_dict(),
            "parity_verified": self.parity_verified,
            "only_feature_flags_differ": self.only_feature_flags_differ,
        }
