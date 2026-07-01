"""Foundation-07.1 Scene Memory Engine."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .contracts import SceneMemoryEntry
from .memory_store import IntelligenceMemoryStore


class SceneMemoryEngine:
    """Scene tracking service for location, timeline, and participant continuity."""

    def __init__(self, store: IntelligenceMemoryStore) -> None:
        self.store = store
        self._scene_order: List[str] = []

    def remember(
        self,
        scene_id: str,
        summary: str,
        location: str = "",
        timeline: str = "",
        participants: Optional[Iterable[str]] = None,
    ) -> SceneMemoryEntry:
        entry = self.store.add_scene(
            scene_id=scene_id,
            summary=summary,
            location=location,
            timeline=timeline,
            participants=participants,
        )
        if scene_id not in self._scene_order:
            self._scene_order.append(scene_id)
        return entry

    def current(self) -> Optional[SceneMemoryEntry]:
        if not self._scene_order:
            return None
        return self.store._scenes.get(self._scene_order[-1])

    def find_by_participant(self, participant: str) -> List[Dict[str, object]]:
        return [
            scene.to_dict()
            for scene in self.store._scenes.values()
            if participant in scene.participants
        ]

    def build_prompt_scenes(self, limit: int = 10) -> List[Dict[str, object]]:
        ordered = [self.store._scenes[key] for key in self._scene_order if key in self.store._scenes]
        return [entry.to_dict() for entry in ordered[-limit:]]
