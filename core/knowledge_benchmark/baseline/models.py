"""
Baseline Models (RM-5.8.5)

Immutable data models for baseline management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import hashlib
import json
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_hash(obj: Any) -> str:
    serialized = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


class BaselineStatus(str, Enum):
    ACTIVE = "active"
    PROMOTED = "promoted"
    ROLLED_BACK = "rolled_back"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class BaselineMetricSnapshot:
    extractor_type: str
    metric_name: str
    value: float
    target: float
    passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extractor_type": self.extractor_type,
            "metric_name": self.metric_name,
            "value": round(self.value, 4),
            "target": round(self.target, 4),
            "passed": self.passed,
        }


@dataclass(frozen=True)
class BaselineEntry:
    baseline_id: str
    run_id: str
    overall_score: float
    grade: str
    extractor_scores: Dict[str, float] = field(default_factory=dict)
    metric_snapshots: List[BaselineRecordSnapshot] = field(default_factory=list)
    timestamp: str = field(default_factory=utc_now_iso)
    promoted_at: str = field(default_factory=utc_now_iso)
    promoted_by: str = "auto"
    status: BaselineStatus = BaselineStatus.ACTIVE
    notes: str = ""
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash:
            hash_input = {
                "run_id": self.run_id,
                "overall_score": self.overall_score,
                "grade": self.grade,
                "extractor_scores": dict(self.extractor_scores),
            }
            object.__setattr__(self, "content_hash", compute_hash(hash_input))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_id": self.baseline_id,
            "run_id": self.run_id,
            "overall_score": self.overall_score,
            "grade": self.grade,
            "extractor_scores": dict(self.extractor_scores),
            "metric_snapshots": [s.to_dict() for s in self.metric_snapshots],
            "timestamp": self.timestamp,
            "promoted_at": self.promoted_at,
            "status": self.status.value,
            "notes": self.notes,
            "content_hash": self.content_hash,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass(frozen=True)
class BaselineRecordSnapshot:
    extractor_type: str
    metric_name: str
    score: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extractor_type": self.extractor_type,
            "metric_name": self.metric_name,
            "score": round(self.score, 4),
            "details": dict(self.details),
        }


BaselineRecord = BaselineRecordSnapshot


@dataclass
class BaselineIndex:
    baselines: List[BaselineEntry] = field(default_factory=list)
    active_id: str = ""
    previous_id: str = ""

    def add_entry(self, entry: BaselineEntry) -> None:
        if not any(b.baseline_id == entry.baseline_id for b in self.baselines):
            self.baselines.append(entry)

        self.previous_id = self.active_id
        self.active_id = entry.baseline_id

    def get_active(self) -> Optional[BaselineEntry]:
        for b in self.baselines:
            if b.baseline_id == self.active_id:
                return b
        return None

    def get_previous(self) -> Optional[BaselineEntry]:
        for b in self.baselines:
            if b.baseline_id == self.previous_id:
                return b
        return None

    def find(self, baseline_id: str) -> Optional[BaselineEntry]:
        for b in self.baselines:
            if b.baseline_id == baseline_id:
                return b
        return None

    def rollback(self) -> Optional[BaselineEntry]:
        if self.previous_id:
            self.active_id = self.previous_id
            return self.get_active()
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entries": [b.to_dict() for b in self.baselines],
            "active_id": self.active_id,
            "previous_id": self.previous_id,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)