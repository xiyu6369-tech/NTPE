from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .evidence import EVIDENCE_SCHEMA_VERSION, TranslationEvidence


@dataclass(frozen=True)
class TranslationEvidenceResult:
    evidence: tuple[TranslationEvidence, ...]
    confidence: float
    reliable: bool
    statistics: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "evidence": [item.to_dict() for item in self.evidence],
            "confidence": self.confidence,
            "reliable": self.reliable,
            "statistics": dict(self.statistics),
            "metadata": dict(self.metadata),
        }
