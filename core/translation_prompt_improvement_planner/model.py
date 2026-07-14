from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .config import IMPLEMENTATION_STATUS


@dataclass(frozen=True)
class PromptImprovementPlan:
    plan_id: str
    related_defect_ids: tuple[str, ...]
    target_prompt_section: str
    problem_statement: str
    suggested_change: str
    expected_benefit: str
    potential_risk: str
    risk_level: str
    priority: str
    verification_method: str
    requires_human_approval: bool = True
    implementation_status: str = IMPLEMENTATION_STATUS

    def __post_init__(self) -> None:
        object.__setattr__(self, "related_defect_ids", tuple(self.related_defect_ids))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["related_defect_ids"] = list(self.related_defect_ids)
        return payload
