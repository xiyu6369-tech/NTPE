"""
Quality Decision Model (RM-5.9.1)

Standardized data models for runtime quality gate integration.
Deterministic and immutable where appropriate.

Zero external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import json


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class QualityStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    RETRY_REQUIRED = "RETRY_REQUIRED"


@dataclass
class TranslationInput:
    source_text: str
    translated_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeExtractionOutput:
    source_text: str
    extracted_entities: List[Dict[str, Any]]
    extractor_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GateInput:
    scorecard: Dict[str, Any] = field(default_factory=dict)
    regression_gate_report: Optional[Dict[str, Any]] = None
    baseline_score: Optional[float] = None


@dataclass
class QualityScorecard:
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    ece: float = 0.0
    overall_score: float = 0.0
    grade: str = "F"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "ece": round(self.ece, 4),
            "overall_score": round(self.overall_score, 4),
            "grade": self.grade,
        }


@dataclass
class QualityDecision:
    status: QualityStatus = QualityStatus.PASS
    scorecard: QualityScorecard = field(default_factory=QualityScorecard)
    reason: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    regression_status: str = "PASS"
    release_decision: str = "ALLOW"
    generated_at: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "scorecard": self.scorecard.to_dict(),
            "reason": list(self.reason),
            "recommendations": list(self.recommendations),
            "regression_status": self.regression_status,
            "release_decision": self.release_decision,
            "generated_at": self.generated_at,
            "metadata": dict(self.metadata),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @property
    def pass_gate(self) -> bool:
        return self.status in (QualityStatus.PASS, QualityStatus.WARNING)

    @property
    def requires_retry(self) -> bool:
        return self.status == QualityStatus.RETRY_REQUIRED