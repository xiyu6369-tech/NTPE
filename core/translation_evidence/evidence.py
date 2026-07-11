from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

EVIDENCE_SCHEMA_VERSION = "6.0.0-stage11.1"
EVIDENCE_TYPES = ("paragraph", "sentence", "dialogue", "terminology", "narrative")


def _bounded_confidence(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 0.0
    return max(0.0, min(1.0, score))


@dataclass(frozen=True)
class TranslationEvidence:
    code: str
    evidence_type: str
    confidence: float
    reliable: bool
    source_start: int | None = None
    source_end: int | None = None
    translated_start: int | None = None
    translated_end: int | None = None
    source_evidence: str = ""
    translated_evidence: str = ""
    paragraph_indexes: tuple[int, ...] = ()
    sentence_indexes: tuple[int, ...] = ()
    detector: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        kind = str(self.evidence_type or "").strip().lower()
        if kind not in EVIDENCE_TYPES:
            raise ValueError(f"unsupported evidence_type: {kind}")
        object.__setattr__(self, "evidence_type", kind)
        object.__setattr__(self, "code", str(self.code or "").strip().upper())
        object.__setattr__(self, "confidence", _bounded_confidence(self.confidence))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def has_source_range(self) -> bool:
        return self.source_start is not None and self.source_end is not None and self.source_end > self.source_start

    @property
    def has_translated_range(self) -> bool:
        return self.translated_start is not None and self.translated_end is not None and self.translated_end >= self.translated_start

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "code": self.code,
            "evidence_type": self.evidence_type,
            "confidence": self.confidence,
            "reliable": bool(self.reliable),
            "source_start": self.source_start,
            "source_end": self.source_end,
            "translated_start": self.translated_start,
            "translated_end": self.translated_end,
            "source_evidence": self.source_evidence,
            "translated_evidence": self.translated_evidence,
            "paragraph_indexes": list(self.paragraph_indexes),
            "sentence_indexes": list(self.sentence_indexes),
            "detector": self.detector,
            "metadata": dict(self.metadata),
        }


ParagraphEvidence = TranslationEvidence
SentenceEvidence = TranslationEvidence
DialogueEvidence = TranslationEvidence
TerminologyEvidence = TranslationEvidence
NarrativeEvidence = TranslationEvidence
