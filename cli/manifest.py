from __future__ import annotations

from typing import Any, Dict, MutableMapping


def build_cli_manifest() -> Dict[str, Any]:
    return {
        "name": "NTPE CLI Core",
        "stage": "NTPE 1.0 Beta Stage-06.0",
        "version": "0.6.0",
        "status": "beta",
        "commands": ["version", "doctor"],
        "capabilities": [
            "cli_context",
            "cli_result",
            "command_registry",
            "argparse_parser",
            "version_command",
            "doctor_command",
            "module_entrypoint",
        ],
        "foundation_compatibility": "foundation-v1.0 frozen compatible",
        "backward_compatible": True,
    }


def attach_cli_manifest(payload: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    payload.setdefault("manifests", {})["cli"] = build_cli_manifest()
    return payload
