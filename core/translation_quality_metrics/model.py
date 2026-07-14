from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class QualityMetric:
    dimension: str
    score: float
    weight: float
    status: str
    related_defect_ids: tuple[str, ...]
    evidence_count: int
    blocking_defect_count: int
    rationale: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "related_defect_ids", tuple(self.related_defect_ids))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["related_defect_ids"] = list(self.related_defect_ids)
        return payload
