from __future__ import annotations

from typing import Any, Dict, MutableMapping


def build_cli_manifest() -> Dict[str, Any]:
    return {
        "name": "NTPE CLI",
        "stage": "NTPE 1.0 Beta Stage-06.2",
        "version": "0.6.2",
        "status": "beta",
        "commands": ["version", "doctor", "translate", "project"],
        "capabilities": [
            "cli_context",
            "cli_result",
            "command_registry",
            "argparse_parser",
            "version_command",
            "doctor_command",
            "module_entrypoint",
            "translate_command",
            "translate_file",
            "translate_folder",
            "translate_resume",
            "translate_report",
            "project_command",
            "project_create",
            "project_open",
            "project_info",
            "project_validate",
            "project_list",
            "project_export",
            "project_import",
        ],
        "foundation_compatibility": "foundation-v1.0 frozen compatible",
        "backward_compatible": True,
    }


def attach_cli_manifest(payload: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    payload.setdefault("manifests", {})["cli"] = build_cli_manifest()
    return payload
