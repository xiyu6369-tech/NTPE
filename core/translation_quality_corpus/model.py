from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class GoldenReviewCase:
    case_id: str
    source_excerpt: str | None
    bad_translation: str | None
    preferred_direction: str
    reason: str
    categories: tuple[str, ...]
    severity: str
    human_confirmed: bool
    approved_final_translation: None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
