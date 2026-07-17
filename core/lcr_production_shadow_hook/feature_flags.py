from __future__ import annotations

import os
from typing import Mapping


GLOBAL_FLAG = "LCR_SHADOW_ENABLED"
KILL_SWITCH = "LCR_KILL_SWITCH"
CHARACTER_MEMORY_FLAG = "LCR_CHARACTER_MEMORY_SHADOW"
CONTEXT_SCENE_FLAG = "LCR_CONTEXT_SCENE_SHADOW"
DUAL_PASS_SEMANTIC_FLAG = "LCR_DUAL_PASS_SEMANTIC_SHADOW"
PRODUCTION_SHADOW_ALIAS = "LCR_PRODUCTION_SHADOW"
SHADOW_KILL_SWITCH_ALIAS = "LCR_SHADOW_KILL_SWITCH"


def _parse(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def resolve_hook_flags(values: Mapping[str, object] | None = None) -> dict[str, bool]:
    try:
        source: Mapping[str, object] = values if values is not None else os.environ
        kill_value = source.get(SHADOW_KILL_SWITCH_ALIAS) if SHADOW_KILL_SWITCH_ALIAS in source else source.get(KILL_SWITCH)
        global_value = source.get(PRODUCTION_SHADOW_ALIAS) if PRODUCTION_SHADOW_ALIAS in source else source.get(GLOBAL_FLAG)
        kill_switch = _parse(kill_value, default=True)
        shadow_enabled = _parse(global_value, default=False)
        character_memory_enabled = _parse(source.get(CHARACTER_MEMORY_FLAG), default=False)
        context_scene_enabled = _parse(source.get(CONTEXT_SCENE_FLAG), default=False)
        dual_pass_semantic_enabled = _parse(source.get(DUAL_PASS_SEMANTIC_FLAG), default=False)
    except Exception:
        return {GLOBAL_FLAG: False, CHARACTER_MEMORY_FLAG: False, CONTEXT_SCENE_FLAG: False, DUAL_PASS_SEMANTIC_FLAG: False, KILL_SWITCH: True}
    if kill_switch:
        shadow_enabled = False
    if not shadow_enabled:
        character_memory_enabled = False
        context_scene_enabled = False
        dual_pass_semantic_enabled = False
    return {
        GLOBAL_FLAG: shadow_enabled,
        CHARACTER_MEMORY_FLAG: character_memory_enabled,
        CONTEXT_SCENE_FLAG: context_scene_enabled,
        DUAL_PASS_SEMANTIC_FLAG: dual_pass_semantic_enabled,
        KILL_SWITCH: kill_switch,
    }


def minimal_shadow_flags() -> dict[str, bool]:
    return {
        "LCR_SHADOW_ENABLED": True,
        "LCR_CHARACTER_MEMORY_SHADOW": False,
        "LCR_CONTEXT_SCENE_SHADOW": False,
        "LCR_DUAL_PASS_SEMANTIC_SHADOW": False,
        "LCR_CHUNK_CACHE_SHADOW": True,
        "LCR_DUAL_PASS_SHADOW": False,
        "LCR_SEMANTIC_VERIFICATION_SHADOW": False,
        "LCR_MULTILINGUAL_PROFILE_SHADOW": True,
        "LCR_PROVIDER_ROUTING_SHADOW": True,
        "LCR_KILL_SWITCH": False,
    }
