from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

CLI_V1_VERSION = "1.0-beta-cli-v1"
CLI_FREEZE_STAGE = "NTPE 1.0 Beta Stage-06.9"

STABLE_COMMANDS: List[str] = [
    "version",
    "doctor",
    "translate",
    "project",
    "benchmark",
    "quality",
    "session",
    "config",
    "plugin",
]

STABLE_JSON_KEYS: List[str] = ["ok", "exit_code", "message", "data", "errors"]

STABLE_OUTPUT_FORMATS: List[str] = ["text", "json"]

STABLE_SUBCOMMANDS: Dict[str, List[str]] = {
    "project": ["create", "open", "info", "validate", "list", "export", "import"],
    "benchmark": ["run", "runtime", "provider", "stress", "report", "compare"],
    "quality": ["check", "score", "repair", "report", "rules"],
    "session": ["create", "list", "info", "resume", "pause", "stop", "checkpoint", "restore", "cleanup"],
    "config": ["list", "get", "set", "validate", "export", "import", "reset"],
    "plugin": ["list", "info", "enable", "disable", "install", "uninstall", "validate"],
}

COMMAND_SUMMARY: Dict[str, Dict[str, Any]] = {
    "version": {"kind": "core", "stable": True},
    "doctor": {"kind": "core", "stable": True},
    "translate": {"kind": "translation", "stable": True},
    "project": {"kind": "project", "stable": True, "subcommands": STABLE_SUBCOMMANDS["project"]},
    "benchmark": {"kind": "benchmark", "stable": True, "subcommands": STABLE_SUBCOMMANDS["benchmark"]},
    "quality": {"kind": "quality", "stable": True, "subcommands": STABLE_SUBCOMMANDS["quality"]},
    "session": {"kind": "session", "stable": True, "subcommands": STABLE_SUBCOMMANDS["session"]},
    "config": {"kind": "config", "stable": True, "subcommands": STABLE_SUBCOMMANDS["config"]},
    "plugin": {"kind": "plugin", "stable": True, "subcommands": STABLE_SUBCOMMANDS["plugin"]},
}

FREEZE_POLICY: Dict[str, Any] = {
    "status": "frozen",
    "allowed_changes": [
        "bug_fix",
        "security_fix",
        "documentation",
        "test_improvement",
        "backward_compatible_extension",
    ],
    "disallowed_changes": [
        "breaking_command_rename",
        "breaking_option_change",
        "breaking_json_schema_change",
        "breaking_exit_code_change",
    ],
}


def build_cli_baseline() -> Dict[str, Any]:
    return {
        "name": "NTPE CLI Baseline",
        "version": CLI_V1_VERSION,
        "stage": CLI_FREEZE_STAGE,
        "status": "stable",
        "commands": list(STABLE_COMMANDS),
        "subcommands": deepcopy(STABLE_SUBCOMMANDS),
        "json_keys": list(STABLE_JSON_KEYS),
        "output_formats": list(STABLE_OUTPUT_FORMATS),
        "command_summary": deepcopy(COMMAND_SUMMARY),
        "freeze_policy": deepcopy(FREEZE_POLICY),
        "foundation_compatibility": "foundation-v1.0 frozen compatible",
        "backward_compatible": True,
    }


def command_is_stable(command: str) -> bool:
    return command in STABLE_COMMANDS


def expected_commands() -> List[str]:
    return list(STABLE_COMMANDS)
