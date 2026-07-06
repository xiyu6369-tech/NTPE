# =====================================================
# NTPE 1.2 Professional
# Stage-16.2 Narrative Intelligence
# =====================================================

from __future__ import annotations

from typing import Iterable, Sequence

from .narrative_context import NarrativeContext
from .narrative_events import NARRATIVE_ANALYZED, NARRATIVE_COMPLETED, NARRATIVE_STARTED, NarrativeEventBus
from .narrative_exceptions import NarrativeInputError
from .narrative_pipeline import NarrativePipeline
from .narrative_result import NarrativeIntelligenceResult, NarrativeSegment
from .narrative_rules import split_segments
from .narrative_state import NarrativeState


class NarrativeIntelligenceEngine:
    """Public Stage-16.2 facade for narrative intelligence analysis."""

    stage = "Stage-16.2"
    name = "Narrative Intelligence Engine"

    def __init__(self, *, event_bus: NarrativeEventBus | None = None) -> None:
        self.event_bus = event_bus or NarrativeEventBus()
        self.state = NarrativeState()
        self.pipeline = NarrativePipeline()

    def build_segment(self, text: str, *, segment_id: str, kind: str = "narration", speaker: str | None = None, **metadata: object) -> NarrativeSegment:
        if not text or not text.strip():
            raise NarrativeInputError("Narrative segment text must not be empty.")
        return NarrativeSegment(segment_id=segment_id, text=text.strip(), kind=kind, speaker=speaker, metadata=dict(metadata))

    def analyze(self, segments: Iterable[NarrativeSegment]) -> NarrativeIntelligenceResult:
        materialized = list(segments)
        self.event_bus.emit(NARRATIVE_STARTED, segment_count=len(materialized))
        result = self.pipeline.run(materialized)
        self.state.update(
            perspective=result.perspective,
            voice=result.voice,
            tense=result.tense,
            emotional_tone=result.emotional_tone,
            transitions=result.scene_transitions,
        )
        self.event_bus.emit(NARRATIVE_ANALYZED, perspective=result.perspective, voice=result.voice, tense=result.tense)
        self.event_bus.emit(NARRATIVE_COMPLETED, segment_count=result.segment_count, finding_count=len(result.findings))
        return result

    def analyze_text(self, text: str, *, context_id: str = "runtime") -> NarrativeIntelligenceResult:
        if not text or not text.strip():
            raise NarrativeInputError("Narrative text must not be empty.")
        context = NarrativeContext(context_id=context_id)
        context.extend(split_segments(text))
        return self.analyze(context.segments)

    def analyze_texts(self, texts: Sequence[str], *, source: str = "runtime") -> NarrativeIntelligenceResult:
        segments = [
            NarrativeSegment(segment_id=f"nar_{index + 1}", text=text.strip(), kind="narration", metadata={"source": source})
            for index, text in enumerate(texts)
            if text and text.strip()
        ]
        return self.analyze(segments)
