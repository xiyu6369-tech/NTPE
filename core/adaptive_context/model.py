from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, Mapping
import math

ContextKind = Literal["character", "dialogue", "narrative", "glossary", "scene", "other"]


@dataclass(frozen=True)
class ContextItem:
    item_id: str
    kind: ContextKind
    content: str
    characters: tuple[str, ...] = ()
    recency: float = 0.0
    relevance: float = 0.0
    continuity: float = 0.0
    required: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.item_id).strip():
            raise ValueError("context item_id must not be blank")
        for name in ("recency", "relevance", "continuity"):
            if not math.isfinite(float(getattr(self, name))):
                raise ValueError(f"context {name} must be finite")
        object.__setattr__(self, "characters", tuple(self.characters))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class RankedContext:
    item: ContextItem
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class SelectedContext:
    item_id: str
    kind: ContextKind
    content: str
    estimated_tokens: int
    score: float
    preserved: bool
    compressed: bool


@dataclass(frozen=True)
class AdaptiveContextResult:
    version: str
    selected: tuple[SelectedContext, ...]
    omitted_ids: tuple[str, ...]
    token_budget: int
    estimated_tokens: int
    fingerprint: str
    observability: Mapping[str, object]
    admissible: bool = True
    fallback_required: bool = False
    fallback_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "selected", tuple(self.selected))
        object.__setattr__(self, "omitted_ids", tuple(self.omitted_ids))
        object.__setattr__(self, "observability", MappingProxyType(dict(self.observability)))
        object.__setattr__(self, "fallback_reasons", tuple(self.fallback_reasons))
