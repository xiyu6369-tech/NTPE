from __future__ import annotations

from typing import Mapping


SHADOW_FLAGS = (
    "LCR_SHADOW_ENABLED",
    "LCR_CHARACTER_MEMORY_SHADOW",
    "LCR_CONTEXT_SCENE_SHADOW",
    "LCR_CHUNK_CACHE_SHADOW",
    "LCR_DUAL_PASS_SHADOW",
    "LCR_SEMANTIC_VERIFICATION_SHADOW",
    "LCR_MULTILINGUAL_PROFILE_SHADOW",
    "LCR_PROVIDER_ROUTING_SHADOW",
)
KILL_SWITCH = "LCR_KILL_SWITCH"
DEFAULT_FLAGS = {**{name: False for name in SHADOW_FLAGS}, KILL_SWITCH: True}


def parse_flag(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"1", "true", "yes", "on"}:
        return True
    if isinstance(value, str) and value.strip().lower() in {"0", "false", "no", "off"}:
        return False
    return default


def resolve_feature_flags(values: Mapping[str, object] | None = None) -> dict[str, bool]:
    values = values or {}
    resolved = {
        name: parse_flag(values.get(name), default=DEFAULT_FLAGS[name])
        for name in (*SHADOW_FLAGS, KILL_SWITCH)
    }
    if resolved[KILL_SWITCH]:
        for name in SHADOW_FLAGS:
            resolved[name] = False
    return resolved
