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
        focus = self._derive_focus(result)
        self.state.update(
            perspective=result.perspective,
            voice=result.voice,
            tense=result.tense,
            emotional_tone=result.emotional_tone,
            transitions=result.scene_transitions,
            focus=focus,
        )
        self.event_bus.emit(NARRATIVE_ANALYZED, perspective=result.perspective, voice=result.voice, tense=result.tense)
        self.event_bus.emit(NARRATIVE_COMPLETED, segment_count=result.segment_count, finding_count=len(result.findings))
        return result

    def _derive_focus(self, result: NarrativeIntelligenceResult) -> str:
        parts = []
        if result.scene_transitions:
            parts.append(f"scene_transitions={len(result.scene_transitions)}")
        if result.style_profile.get("dominant_mode"):
            parts.append(f"mode={result.style_profile['dominant_mode']}")
        if result.style_profile.get("dialogue_density", 0) > 0.5:
            parts.append("dialogue_heavy")
        return "; ".join(parts) if parts else ""

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

    def analyze_chunk(self, source: str, translation: str = "") -> NarrativeIntelligenceResult:
        """Analyze a single chunk and update cross-chunk narrative state.

        Args:
            source: Source text chunk to analyze
            translation: Optional previous translation for context (currently unused but reserved)

        Returns:
            NarrativeIntelligenceResult with analysis of the chunk
        """
        return self.analyze_text(source, context_id=f"chunk_{self.state.counters.get('updates', 0) + 1}")

    def get_context_for_prompt(self) -> dict:
        """Return current narrative state formatted for PromptAssembly Narrative section."""
        return self.state.to_prompt_context()

    def get_state_for_checkpoint(self) -> dict:
        """Return current narrative state for checkpoint serialization."""
        return self.state.to_dict()

    def restore_state_from_checkpoint(self, state_dict: dict) -> None:
        """Restore narrative state from checkpoint data."""
        self.state = NarrativeState.from_dict(state_dict)
