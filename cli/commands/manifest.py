from __future__ import annotations

from typing import Any, Dict


def build_translate_manifest() -> Dict[str, Any]:
    return {
        "component": "cli.translate",
        "version": "1.0-beta-stage-06.1",
        "commands": ["translate"],
        "options": [
            "input",
            "--output",
            "--resume",
            "--provider",
            "--quality",
            "--dry-run",
            "--pattern",
            "--overwrite",
            "--suffix",
        ],
        "compatible_with": [
            "foundation-v1.0",
            "beta-stage-01",
            "beta-stage-02",
            "beta-stage-03",
            "beta-stage-04",
            "beta-stage-05",
            "beta-stage-06.0",
        ],
    }


def attach_translate_manifest(payload: Dict[str, Any]) -> Dict[str, Any]:
    manifests = payload.setdefault("manifests", {})
    manifests["cli_translate"] = build_translate_manifest()
    return payload
