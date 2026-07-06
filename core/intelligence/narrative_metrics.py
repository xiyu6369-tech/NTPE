# =====================================================
# NTPE 1.2 Professional
# Stage-16.2 Narrative Intelligence
# =====================================================

from __future__ import annotations

from typing import Any, Dict

from .narrative_result import NarrativeIntelligenceResult


def build_narrative_metrics(result: NarrativeIntelligenceResult) -> Dict[str, Any]:
    total = max(result.segment_count, 1)
    return {
        "segment_count": result.segment_count,
        "dialogue_count": result.dialogue_count,
        "dialogue_ratio": round(result.dialogue_count / total, 4),
        "finding_count": len(result.findings),
        "scene_transition_count": len(result.scene_transitions),
        "perspective": result.perspective,
        "voice": result.voice,
        "tense": result.tense,
        "emotional_tone": result.emotional_tone,
    }
