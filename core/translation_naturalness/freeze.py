from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Mapping

NATURALNESS_FREEZE_VERSION: Final[str] = "6.0.0-stage12.5"
NATURALNESS_FROZEN_STAGES: Final[tuple[str, ...]] = ("12.1", "12.2", "12.3", "12.4", "12.4.1")


@dataclass(frozen=True)
class TranslationNaturalnessFreeze:
    version: str = NATURALNESS_FREEZE_VERSION
    frozen_stages: tuple[str, ...] = NATURALNESS_FROZEN_STAGES
    prompt_policy_frozen: bool = True
    canonicalization_frozen: bool = True
    hallucination_guard_frozen: bool = True
    collocation_guard_frozen: bool = True
    voice_register_guard_frozen: bool = True
    discipline_mapping_frozen: bool = True
    semantic_rewrite_forbidden: bool = True
    provider_behavior_unchanged: bool = True
    quality_contract_unchanged: bool = True
    rollback_supported: bool = True
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({
        "frozen": True,
        "safe_canonicalization_only": True,
        "semantic_rewrite_allowed": False,
        "voice_register_nonblocking": True,
        "unsupported_detail_high_confidence_blocking": True,
        "provider_calls_added": 0,
        "provider_client_created": False,
        "http_requests_added": 0,
        "nvidia_rpm_ceiling": 40,
        "rollback_environment_variable": "NTPE_NATURALNESS_POLICY",
        "runtime_wiring_added": False,
    }))

    def __post_init__(self) -> None:
        object.__setattr__(self, "frozen_stages", tuple(self.frozen_stages))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_metadata(self) -> dict[str, object]:
        return {
            "version": self.version,
            "frozen": True,
            "frozen_stages": list(self.frozen_stages),
            "prompt_policy_frozen": self.prompt_policy_frozen,
            "canonicalization_frozen": self.canonicalization_frozen,
            "hallucination_guard_frozen": self.hallucination_guard_frozen,
            "collocation_guard_frozen": self.collocation_guard_frozen,
            "voice_register_guard_frozen": self.voice_register_guard_frozen,
            "discipline_mapping_frozen": self.discipline_mapping_frozen,
            "semantic_rewrite_forbidden": self.semantic_rewrite_forbidden,
            "provider_behavior_unchanged": self.provider_behavior_unchanged,
            "quality_contract_unchanged": self.quality_contract_unchanged,
            "rollback_supported": self.rollback_supported,
            **dict(self.metadata),
        }


def build_translation_naturalness_freeze() -> TranslationNaturalnessFreeze:
    return TranslationNaturalnessFreeze()
