from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .location import DefectLocation


@dataclass(frozen=True)
class TranslationDefect:
    defect_id: str
    category: str
    secondary_categories: tuple[str, ...]
    severity: str
    source_location: DefectLocation
    translation_location: DefectLocation
    source_excerpt: str | None
    translation_excerpt: str | None
    expected_behavior: str
    suggested_revision: str | None
    reason: str
    confidence: float
    review_origin: str
    human_confirmed: bool
    blocking: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "secondary_categories", tuple(self.secondary_categories))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
