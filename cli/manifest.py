from __future__ import annotations

from typing import Any, Dict, MutableMapping


def build_cli_manifest() -> Dict[str, Any]:
    return {
        "name": "NTPE CLI",
        "stage": "NTPE 1.0 Beta Stage-06.5",
        "version": "0.6.5",
        "status": "beta",
        "commands": ["version", "doctor", "translate", "project", "benchmark", "quality", "session"],
        "capabilities": [
            "cli_context",
            "cli_result",
            "command_registry",
            "argparse_parser",
            "version_command",
            "doctor_command",
            "translate_command",
            "project_command",
            "benchmark_command",
            "quality_command",
            "session_command",
            "session_list",
            "session_info",
            "session_resume",
            "session_pause",
            "session_stop",
            "session_checkpoint",
            "session_restore",
            "session_cleanup",
            "json_output",
            "module_entrypoint",
        ],
        "foundation_compatibility": "foundation-v1.0 frozen compatible",
        "backward_compatible": True,
    }


def attach_cli_manifest(payload: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    payload.setdefault("manifests", {})["cli"] = build_cli_manifest()
    return payload
