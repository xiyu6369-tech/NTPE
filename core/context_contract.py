"""
NTPE Foundation-04.3
Pipeline Context Contract Stabilization

This module is additive and backward-compatible.
It provides a stable validation and normalization layer for pipeline payload/context
objects after Foundation-04.2 Context Migration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, MutableMapping, Optional
from copy import deepcopy


class NTPEContextContractError(Exception):
    """Raised when a pipeline context payload violates the stable NTPE contract."""


@dataclass(frozen=True)
class ContextContractResult:
    ok: bool
    payload: Dict[str, Any]
    warnings: tuple[str, ...] = field(default_factory=tuple)


REQUIRED_TOP_LEVEL_KEYS = (
    "source_text",
    "target_language",
    "context",
    "metadata",
)

DEFAULT_CONTEXT = {
    "previous_text": "",
    "previous_translation": "",
    "glossary": {},
    "character_memory": {},
    "narrative_state": {},
}

DEFAULT_METADATA = {
    "engine": "NTPE",
    "foundation": "04.3",
    "stage": "context_contract",
}


def _as_dict(value: Any, key: str) -> Dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise NTPEContextContractError(f"{key} must be a dict")
    return value


def normalize_context_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Normalize a migrated pipeline payload into the stable Foundation-04.3 contract.

    Backward compatibility:
    - Missing context/metadata are created.
    - Existing unknown keys are preserved.
    - Existing context/metadata subkeys are preserved.
    """
    if payload is None:
        raise NTPEContextContractError("payload must not be None")
    if not isinstance(payload, Mapping):
        raise NTPEContextContractError("payload must be a mapping")

    normalized: Dict[str, Any] = deepcopy(dict(payload))

    if "source_text" not in normalized:
        normalized["source_text"] = normalized.get("text", "")

    if "target_language" not in normalized:
        normalized["target_language"] = normalized.get("language", "繁體中文")

    context = deepcopy(DEFAULT_CONTEXT)
    context.update(_as_dict(normalized.get("context"), "context"))
    normalized["context"] = context

    metadata = deepcopy(DEFAULT_METADATA)
    metadata.update(_as_dict(normalized.get("metadata"), "metadata"))
    normalized["metadata"] = metadata

    return normalized


def validate_context_payload(payload: Mapping[str, Any]) -> ContextContractResult:
    """
    Validate and normalize a payload.

    This function intentionally returns a result object instead of mutating input.
    """
    warnings: list[str] = []
    normalized = normalize_context_payload(payload)

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in normalized:
            raise NTPEContextContractError(f"missing required key: {key}")

    if not isinstance(normalized["source_text"], str):
        raise NTPEContextContractError("source_text must be str")

    if not isinstance(normalized["target_language"], str):
        raise NTPEContextContractError("target_language must be str")

    if not normalized["target_language"].strip():
        warnings.append("target_language is empty after stripping")

    if not normalized["source_text"]:
        warnings.append("source_text is empty")

    return ContextContractResult(
        ok=True,
        payload=normalized,
        warnings=tuple(warnings),
    )


def merge_context_payload(base_payload: Mapping[str, Any], patch_payload: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Merge two payloads while preserving stable context and metadata structures.
    Patch values override base values.
    """
    base = normalize_context_payload(base_payload)
    patch = normalize_context_payload(patch_payload)

    merged = deepcopy(base)
    for key, value in patch.items():
        if key == "context":
            merged["context"].update(value)
        elif key == "metadata":
            merged["metadata"].update(value)
        else:
            merged[key] = value

    return normalize_context_payload(merged)
