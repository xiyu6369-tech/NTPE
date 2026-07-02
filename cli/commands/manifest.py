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


def build_benchmark_manifest() -> Dict[str, Any]:
    return {
        "component": "cli.benchmark",
        "version": "1.0-beta-stage-06.3",
        "commands": ["benchmark"],
        "subcommands": ["run", "runtime", "provider", "stress", "report", "compare"],
        "integrates": [
            "benchmark.framework",
            "benchmark.runtime",
            "benchmark.provider",
            "benchmark.stress",
            "benchmark.report",
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
        ],
    }


def attach_benchmark_manifest(payload: Dict[str, Any]) -> Dict[str, Any]:
    manifests = payload.setdefault("manifests", {})
    manifests["cli_benchmark"] = build_benchmark_manifest()
    return payload
