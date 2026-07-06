# =====================================================
# NTPE 1.2 Professional
# Stage-16.2 Narrative Intelligence
# =====================================================

from __future__ import annotations

from statistics import mean
from typing import Any, Dict, Iterable

from .narrative_result import NarrativeSegment


def build_style_profile(segments: Iterable[NarrativeSegment]) -> Dict[str, Any]:
    materialized = list(segments)
    lengths = [len(segment.text.strip()) for segment in materialized if segment.text.strip()]
    dialogue_count = sum(1 for segment in materialized if segment.kind == "dialogue")
    narration_count = sum(1 for segment in materialized if segment.kind == "narration")
    total = max(len(materialized), 1)
    avg_len = float(mean(lengths)) if lengths else 0.0
    density = dialogue_count / total
    if density >= 0.65:
        dominant_mode = "dialogue_heavy"
    elif narration_count / total >= 0.65:
        dominant_mode = "narration_heavy"
    else:
        dominant_mode = "mixed"
    return {
        "segment_count": len(materialized),
        "dialogue_count": dialogue_count,
        "narration_count": narration_count,
        "dialogue_density": round(density, 4),
        "average_segment_length": round(avg_len, 2),
        "dominant_mode": dominant_mode,
    }
