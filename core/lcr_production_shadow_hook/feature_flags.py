from __future__ import annotations

import os
from typing import Mapping


GLOBAL_FLAG = "LCR_SHADOW_ENABLED"
KILL_SWITCH = "LCR_KILL_SWITCH"


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
        kill_switch = _parse(source.get(KILL_SWITCH), default=True)
        shadow_enabled = _parse(source.get(GLOBAL_FLAG), default=False)
    except Exception:
        return {GLOBAL_FLAG: False, KILL_SWITCH: True}
    if kill_switch:
        shadow_enabled = False
    return {GLOBAL_FLAG: shadow_enabled, KILL_SWITCH: kill_switch}


def minimal_shadow_flags() -> dict[str, bool]:
    return {
        "LCR_SHADOW_ENABLED": True,
        "LCR_CHARACTER_MEMORY_SHADOW": False,
        "LCR_CONTEXT_SCENE_SHADOW": False,
        "LCR_CHUNK_CACHE_SHADOW": True,
        "LCR_DUAL_PASS_SHADOW": False,
        "LCR_SEMANTIC_VERIFICATION_SHADOW": False,
        "LCR_MULTILINGUAL_PROFILE_SHADOW": True,
        "LCR_PROVIDER_ROUTING_SHADOW": True,
        "LCR_KILL_SWITCH": False,
    }
