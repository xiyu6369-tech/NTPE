# =====================================================
# NTPE 1.2 Professional
# Stage-16.2 Narrative Intelligence
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class NarrativeSegment:
    segment_id: str
    text: str
    kind: str = "narration"
    speaker: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "text": self.text,
            "kind": self.kind,
            "speaker": self.speaker,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class NarrativeFinding:
    category: str
    severity: str
    message: str
    segment_id: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "segment_id": self.segment_id,
        }


@dataclass
class NarrativeIntelligenceResult:
    segments: List[NarrativeSegment] = field(default_factory=list)
    perspective: str = "unknown"
    voice: str = "neutral"
    tense: str = "undetermined"
    emotional_tone: str = "neutral"
    scene_transitions: List[str] = field(default_factory=list)
    style_profile: Dict[str, Any] = field(default_factory=dict)
    findings: List[NarrativeFinding] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def segment_count(self) -> int:
        return len(self.segments)

    @property
    def dialogue_count(self) -> int:
        return sum(1 for segment in self.segments if segment.kind == "dialogue")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segments": [segment.to_dict() for segment in self.segments],
            "perspective": self.perspective,
            "voice": self.voice,
            "tense": self.tense,
            "emotional_tone": self.emotional_tone,
            "scene_transitions": list(self.scene_transitions),
            "style_profile": dict(self.style_profile),
            "findings": [finding.to_dict() for finding in self.findings],
            "metrics": dict(self.metrics),
        }
