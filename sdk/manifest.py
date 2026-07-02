"""SDK manifest for NTPE 1.0 Beta Stage-07.0."""
from __future__ import annotations

from typing import Any, Dict, MutableMapping, Optional

VERSION = "0.7.0"
STAGE = "NTPE 1.0 Beta Stage-07.0 SDK Core"


def build_sdk_manifest(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": "NTPE SDK",
        "stage": STAGE,
        "version": VERSION,
        "status": "beta",
        "components": [
            "SDKRequest",
            "SDKResult",
            "NTPEClient",
            "client_manifest",
            "translation_engine_bridge",
            "provider_manager_bridge",
        ],
        "capabilities": [
            "translate_text",
            "translate_segments",
            "prompt_package",
            "manifest_export",
            "dict_serialization",
            "callable_translator_injection",
            "provider_manager_injection",
        ],
        "foundation_compatibility": "foundation-v1.0 frozen compatible",
        "cli_compatibility": "stage-06.9 cli freeze compatible",
        "backward_compatible": True,
        "metadata": dict(metadata or {}),
    }


def attach_sdk_manifest(payload: MutableMapping[str, Any], metadata: Optional[Dict[str, Any]] = None) -> MutableMapping[str, Any]:
    payload.setdefault("manifests", {})["sdk"] = build_sdk_manifest(metadata)
    return payload
