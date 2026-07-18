from __future__ import annotations

from dataclasses import dataclass


GLOBAL_FLAG = "--quality-integration-v72"
CHARACTER_FLAG = "--quality-character-memory-v72"
CONTEXT_SCENE_FLAG = "--quality-context-scene-v72"
NATURALNESS_FLAG = "--quality-naturalness-v72"
KILL_SWITCH_FLAG = "--quality-integration-kill-switch-v72"


@dataclass(frozen=True)
class QualityIntegrationFlags:
    integration: bool = False
    character_memory: bool = False
    context_scene: bool = False
    naturalness: bool = False
    kill_switch: bool = False

    @property
    def character_enabled(self) -> bool:
        return not self.kill_switch and (self.integration or self.character_memory)

    @property
    def context_scene_enabled(self) -> bool:
        return not self.kill_switch and (self.integration or self.context_scene)

    @property
    def naturalness_enabled(self) -> bool:
        return not self.kill_switch and (self.integration or self.naturalness)

    @property
    def enabled(self) -> bool:
        return self.character_enabled or self.context_scene_enabled or self.naturalness_enabled

    def to_dict(self) -> dict[str, bool]:
        return {
            "integration": self.integration,
            "character_memory": self.character_memory,
            "context_scene": self.context_scene,
            "naturalness": self.naturalness,
            "kill_switch": self.kill_switch,
        }

