# =====================================================
# NTPE 1.2 Professional
# Stage-15.7 Quality Auto Repair Layer
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class RepairStatus(str, Enum):
    CLEAN = "clean"
    REPAIRED = "repaired"
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass
class RepairAction:
    name: str
    category: str
    description: str
    before_length: int
    after_length: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "before_length": self.before_length,
            "after_length": self.after_length,
            "metadata": dict(self.metadata),
        }


@dataclass
class RepairResult:
    original_text: str
    repaired_text: str
    status: RepairStatus = RepairStatus.CLEAN
    actions: List[RepairAction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def changed(self) -> bool:
        return self.original_text != self.repaired_text

    def add_action(self, action: RepairAction) -> None:
        self.actions.append(action)
        if self.changed:
            self.status = RepairStatus.REPAIRED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "changed": self.changed,
            "original_length": len(self.original_text or ""),
            "repaired_length": len(self.repaired_text or ""),
            "actions": [action.to_dict() for action in self.actions],
            "metadata": dict(self.metadata),
        }
