# =====================================================
# NTPE 1.2 Professional
# Stage-16.2 Narrative Intelligence
# =====================================================

from __future__ import annotations

from typing import Iterable, List

from .narrative_metrics import build_narrative_metrics
from .narrative_profile import build_style_profile
from .narrative_result import NarrativeIntelligenceResult, NarrativeSegment
from .narrative_rules import (
    detect_emotional_tone,
    detect_perspective,
    detect_scene_transitions,
    detect_tense,
    detect_voice,
    validate_narrative_consistency,
)


class NarrativePipeline:
    """Deterministic narrative analysis pipeline for Stage-16.2."""

    def run(self, segments: Iterable[NarrativeSegment]) -> NarrativeIntelligenceResult:
        materialized: List[NarrativeSegment] = [segment for segment in segments if segment.text.strip()]
        text = "\n".join(segment.text for segment in materialized)
        perspective = detect_perspective(text)
        tense = detect_tense(text)
        emotional_tone = detect_emotional_tone(text)
        voice = detect_voice(materialized)
        transitions = detect_scene_transitions(materialized)
        findings = validate_narrative_consistency(materialized, perspective, tense)
        result = NarrativeIntelligenceResult(
            segments=materialized,
            perspective=perspective,
            voice=voice,
            tense=tense,
            emotional_tone=emotional_tone,
            scene_transitions=transitions,
            style_profile=build_style_profile(materialized),
            findings=findings,
        )
        result.metrics = build_narrative_metrics(result)
        return result
