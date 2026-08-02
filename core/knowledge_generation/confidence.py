"""
Confidence Scoring for Knowledge Extraction SDK (RM-5.7.2)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import math


@dataclass
class ConfidenceScore:
    overall: float
    components: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.overall = max(0.0, min(1.0, self.overall))
        for k, v in self.components.items():
            self.components[k] = max(0.0, min(1.0, v))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": self.overall,
            "components": dict(self.components),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfidenceScore":
        return cls(
            overall=data.get("overall", 0.0),
            components=data.get("components", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ConfidenceThresholds:
    minimum: float = 0.0
    low: float = 0.3
    medium: float = 0.5
    high: float = 0.7
    critical: float = 0.9

    def categorize(self, score: float) -> str:
        if score >= self.critical:
            return "critical"
        elif score >= self.high:
            return "high"
        elif score >= self.medium:
            return "medium"
        elif score >= self.low:
            return "low"
        else:
            return "below_minimum"

    def passes(self, score: float, threshold: str = "minimum") -> bool:
        thresholds = {
            "minimum": self.minimum,
            "low": self.low,
            "medium": self.medium,
            "high": self.high,
            "critical": self.critical,
        }
        return score >= thresholds.get(threshold, self.minimum)


class ConfidenceCalculator:
    DEFAULT_WEIGHTS = {
        "pattern_match": 0.3,
        "context_consistency": 0.2,
        "source_reliability": 0.2,
        "cross_reference": 0.15,
        "frequency": 0.15,
    }

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

    def calculate(
        self,
        pattern_match: float = 0.5,
        context_consistency: float = 0.5,
        source_reliability: float = 0.5,
        cross_reference: float = 0.5,
        frequency: float = 0.5,
        custom_signals: Dict[str, float] = None,
    ) -> ConfidenceScore:
        signals = {
            "pattern_match": pattern_match,
            "context_consistency": context_consistency,
            "source_reliability": source_reliability,
            "cross_reference": cross_reference,
            "frequency": frequency,
        }

        if custom_signals:
            signals.update(custom_signals)

        overall = 0.0
        components = {}

        for signal, value in signals.items():
            weight = self.weights.get(signal, 0.0)
            components[signal] = value
            overall += value * weight

        custom_weight = 0.0
        for signal, value in (custom_signals or {}).items():
            if signal not in self.weights:
                custom_weight += value * 0.1

        overall = min(1.0, overall + custom_weight)

        return ConfidenceScore(
            overall=overall,
            components=components,
            metadata={"weights": dict(self.weights)},
        )

    def calculate_from_entity(self, entity: Any) -> ConfidenceScore:
        attrs = entity.attributes if hasattr(entity, "attributes") else {}

        return self.calculate(
            pattern_match=attrs.get("pattern_confidence", 0.5),
            context_consistency=attrs.get("context_confidence", 0.5),
            source_reliability=attrs.get("source_confidence", 0.5),
            cross_reference=attrs.get("reference_confidence", 0.5),
            frequency=min(1.0, attrs.get("frequency", 0) / 10.0),
        )

    def combine_scores(self, scores: List[ConfidenceScore], method: str = "weighted") -> ConfidenceScore:
        if not scores:
            return ConfidenceScore(overall=0.0)

        if method == "maximum":
            overall = max(s.overall for s in scores)
        elif method == "minimum":
            overall = min(s.overall for s in scores)
        elif method == "geometric":
            product = 1.0
            for s in scores:
                product *= max(0.001, s.overall)
            overall = product ** (1.0 / len(scores))
        else:
            overall = sum(s.overall for s in scores) / len(scores)

        components = {}
        for s in scores:
            for k, v in s.components.items():
                if k not in components:
                    components[k] = []
                components[k].append(v)

        merged = {k: sum(v) / len(v) for k, v in components.items()}

        return ConfidenceScore(
            overall=overall,
            components=merged,
            metadata={"method": method, "count": len(scores)},
        )


DEFAULT_THRESHOLDS = ConfidenceThresholds()
DEFAULT_CALCULATOR = ConfidenceCalculator()
