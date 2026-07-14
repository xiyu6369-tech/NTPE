from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class StructuredReview:
    review_id: str
    source_execution_stage: str
    source_artifact_sha256: str
    source_review_sha256: str
    review_type: str
    review_origin: str
    human_review_required: bool
    human_review_completed: bool
    quality_pass: bool
    reviewed_dimensions: tuple[str, ...]
    defect_count: int
    blocking_defect_count: int
    content_redacted: bool
    new_translation_generated: bool = False
    provider_executed_in_this_stage: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "reviewed_dimensions", tuple(self.reviewed_dimensions))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
