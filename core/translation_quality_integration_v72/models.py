from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .flags import QualityIntegrationFlags


@dataclass(frozen=True)
class PromptBudget:
    total_prompt_tokens: int = 4096
    character_tokens: int = 256
    context_tokens: int = 384
    scene_tokens: int = 192
    naturalness_tokens: int = 192


@dataclass(frozen=True)
class QualityIntegrationRequest:
    source_text: str
    base_prompt_tokens: int
    glossary_tokens: int = 0
    flags: QualityIntegrationFlags = field(default_factory=QualityIntegrationFlags)
    budget: PromptBudget = field(default_factory=PromptBudget)
    character_store: Any | None = None
    context_scene_store: Any | None = None
    active_character_ids: Sequence[str] = ()
    chapter_id: str | None = None
    scene_id: str | None = None
    sequence_index: int | None = None
    source_language: str | None = None
    scope: Mapping[str, str] = field(default_factory=dict)
    selection_time: str = "9999-01-01T00:00:00Z"


@dataclass(frozen=True)
class SelectedQualityContext:
    character_items: tuple[Any, ...] = ()
    context_items: tuple[Any, ...] = ()
    scene_items: tuple[Any, ...] = ()
    character_considered: int = 0
    context_considered: int = 0
    character_excluded: Mapping[str, int] = field(default_factory=dict)
    context_dropped: Mapping[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class QualityIntegrationMetadata:
    enabled: bool
    character_records_considered: int
    character_records_selected: int
    context_records_considered: int
    context_records_selected: int
    scene_records_selected: int
    character_tokens: int
    context_tokens: int
    scene_tokens: int
    naturalness_tokens: int
    total_added_tokens: int
    budget_exhausted: bool
    selection_fingerprint: str
    flags: Mapping[str, bool]
    status: str = "applied"

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "character_records_considered": self.character_records_considered,
            "character_records_selected": self.character_records_selected,
            "context_records_considered": self.context_records_considered,
            "context_records_selected": self.context_records_selected,
            "scene_records_selected": self.scene_records_selected,
            "character_tokens": self.character_tokens,
            "context_tokens": self.context_tokens,
            "scene_tokens": self.scene_tokens,
            "naturalness_tokens": self.naturalness_tokens,
            "total_added_tokens": self.total_added_tokens,
            "budget_exhausted": self.budget_exhausted,
            "selection_fingerprint": self.selection_fingerprint,
            "flags": dict(self.flags),
            "status": self.status,
        }


@dataclass(frozen=True)
class QualityIntegrationResult:
    user_prompt: str
    section: str
    metadata: QualityIntegrationMetadata

