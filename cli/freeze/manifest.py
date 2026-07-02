from __future__ import annotations

from typing import Any, Dict, MutableMapping

from .baseline import build_cli_baseline


def build_cli_freeze_manifest() -> Dict[str, Any]:
    baseline = build_cli_baseline()
    return {
        "component": "cli.freeze",
        "version": "1.0-beta-stage-06.9",
        "status": "frozen",
        "baseline": baseline["version"],
        "commands": baseline["commands"],
        "contracts": [
            "command-api",
            "json-output-schema",
            "text-output-format",
            "exit-code-contract",
            "help-output-contract",
            "manifest-contract",
        ],
        "compatible_with": [
            "foundation-v1.0",
            "beta-stage-01",
            "beta-stage-02",
            "beta-stage-03",
            "beta-stage-04",
            "beta-stage-05",
            "beta-stage-06.0",
            "beta-stage-06.1",
            "beta-stage-06.2",
            "beta-stage-06.3",
            "beta-stage-06.4",
            "beta-stage-06.5",
            "beta-stage-06.6",
            "beta-stage-06.7",
            "beta-stage-06.8",
        ],
        "backward_compatible": True,
    }


def attach_cli_freeze_manifest(payload: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    payload.setdefault("manifests", {})["cli_freeze"] = build_cli_freeze_manifest()
    return payload
