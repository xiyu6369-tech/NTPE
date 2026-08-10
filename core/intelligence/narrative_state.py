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
    last_focus: str = ""
    scene_history: List[str] = field(default_factory=list)
    counters: Dict[str, int] = field(default_factory=dict)

    def update(self, *, perspective: str, voice: str, tense: str, emotional_tone: str, transitions: List[str], focus: str = "") -> None:
        self.last_perspective = perspective or self.last_perspective
        self.last_voice = voice or self.last_voice
        self.last_tense = tense or self.last_tense
        self.last_emotional_tone = emotional_tone or self.last_emotional_tone
        if focus:
            self.last_focus = focus
        self.scene_history.extend(transitions)
        self.counters["updates"] = self.counters.get("updates", 0) + 1

    def to_prompt_context(self) -> dict:
        """Return narrative state formatted for PromptAssembly Narrative section."""
        return {
            "perspective": self.last_perspective,
            "voice": self.last_voice,
            "tense": self.last_tense,
            "emotional_tone": self.last_emotional_tone,
            "focus": self.last_focus,
            "transitions": list(self.scene_history),
            "metadata": {
                "updates": self.counters.get("updates", 0),
            },
        }

    def to_dict(self) -> dict:
        """Serialize narrative state for checkpoint/resume."""
        return self.to_prompt_context()

    @classmethod
    def from_dict(cls, data: dict) -> "NarrativeState":
        """Deserialize narrative state from checkpoint/resume."""
        state = cls()
        state.last_perspective = data.get("perspective", "unknown")
        state.last_voice = data.get("voice", "neutral")
        state.last_tense = data.get("tense", "undetermined")
        state.last_emotional_tone = data.get("emotional_tone", "neutral")
        state.last_focus = data.get("focus", "")
        state.scene_history = list(data.get("transitions", []))
        state.counters = dict(data.get("metadata", {}))
        return state
