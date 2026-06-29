from __future__ import annotations

from pathlib import Path

from .context_serializer import ContextSerializer
from .story_state import StoryState
from .character_state import CharacterState
from .scene_state import SceneState
from .dialogue_state import DialogueState
from .narrative_state import NarrativeState
from .context_builder import ContextBuilder


class ContextMemoryEngine:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.serializer = ContextSerializer(self.root)
        self.builder = ContextBuilder(max_chars=1800)

    def load_states(self) -> dict:
        return {
            "story_state": self.serializer.load("story_state.json", {}),
            "character_state": self.serializer.load("character_state.json", {}),
            "scene_state": self.serializer.load("scene_state.json", {}),
            "dialogue_state": self.serializer.load("dialogue_state.json", {}),
            "narrative_state": self.serializer.load("narrative_state.json", {}),
        }

    def build_context(self, previous_tail: str = "") -> dict:
        return self.builder.build(self.load_states(), previous_tail=previous_tail)

    def update_after_chunk(self, *, file_name: str, chunk_index: int, source_text: str, translation_text: str = "") -> dict:
        states = self.load_states()

        story = StoryState(states.get("story_state")).update(
            file_name=file_name,
            chunk_index=chunk_index,
            source_text=source_text,
            translation_text=translation_text,
        )

        character = CharacterState(states.get("character_state")).update(
            source_text=source_text,
            translation_text=translation_text,
        )

        scene = SceneState(states.get("scene_state")).update(
            source_text=source_text,
            translation_text=translation_text,
        )

        dialogue = DialogueState(states.get("dialogue_state")).update(
            source_text=source_text,
            translation_text=translation_text,
        )

        narrative = NarrativeState(states.get("narrative_state")).update(
            source_text=source_text,
            translation_text=translation_text,
        )

        self.serializer.save("story_state.json", story)
        self.serializer.save("character_state.json", character)
        self.serializer.save("scene_state.json", scene)
        self.serializer.save("dialogue_state.json", dialogue)
        self.serializer.save("narrative_state.json", narrative)

        return {
            "story_state": story,
            "character_state": character,
            "scene_state": scene,
            "dialogue_state": dialogue,
            "narrative_state": narrative,
        }
