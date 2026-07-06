# =====================================================
# NTPE 1.2 Professional
# Stage-16.2 Narrative Intelligence
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class NarrativeState:
    """Tracks cross-chunk narrative state without mutating frozen runtime APIs."""

    last_perspective: str = "unknown"
    last_voice: str = "neutral"
    last_tense: str = "undetermined"
    last_emotional_tone: str = "neutral"
    scene_history: List[str] = field(default_factory=list)
    counters: Dict[str, int] = field(default_factory=dict)

    def update(self, *, perspective: str, voice: str, tense: str, emotional_tone: str, transitions: List[str]) -> None:
        self.last_perspective = perspective or self.last_perspective
        self.last_voice = voice or self.last_voice
        self.last_tense = tense or self.last_tense
        self.last_emotional_tone = emotional_tone or self.last_emotional_tone
        self.scene_history.extend(transitions)
        self.counters["updates"] = self.counters.get("updates", 0) + 1
