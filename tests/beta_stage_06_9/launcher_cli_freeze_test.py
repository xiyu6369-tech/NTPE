from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cli.freeze import (
    CLICompatibilityChecker,
    build_cli_baseline,
    build_cli_freeze_manifest,
    command_is_stable,
    run_cli_acceptance,
    run_cli_regression_suite,
)
from cli.main import build_registry, format_result, run_cli
from cli.parser import build_parser
from cli.result import CLIResult


def show(name: str, ok: bool) -> bool:
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    checks = []

    baseline = build_cli_baseline()
    required_commands = [
        "version", "doctor", "translate", "project", "benchmark", "quality", "session", "config", "plugin"
    ]
    registry = build_registry()
    registry_names = registry.names()
    parser_help = build_parser().format_help()
    manifest = build_cli_freeze_manifest()

    checks.append(show("CLI Compatibility", CLICompatibilityChecker().run().ok))
    checks.append(show("Command Registry", all(command in registry_names for command in required_commands)))
    checks.append(show("Command Stability", all(command_is_stable(command) for command in required_commands)))
    checks.append(show("Translate Stable", "translate" in registry_names and "translate" in parser_help))
    checks.append(show("Project Stable", "project" in registry_names and "project" in parser_help))
    checks.append(show("Benchmark Stable", "benchmark" in registry_names and "benchmark" in parser_help))
    checks.append(show("Quality Stable", "quality" in registry_names and "quality" in parser_help))
    checks.append(show("Session Stable", "session" in registry_names and "session" in parser_help))
    checks.append(show("Config Stable", "config" in registry_names and "config" in parser_help))
    checks.append(show("Plugin Stable", "plugin" in registry_names and "plugin" in parser_help))

    json_payload = CLIResult.success("stable", value=1).to_dict()
    encoded = json.dumps(json_payload, ensure_ascii=False)
    decoded = json.loads(encoded)
    checks.append(show("JSON Output Stability", sorted(decoded.keys()) == ["data", "errors", "exit_code", "message", "ok"]))

    version_result = run_cli(["version"])
    checks.append(show("Text Output Stability", "NTPE" in format_result(version_result)))
    checks.append(show("Help Output Stability", all(command in parser_help for command in required_commands)))
    checks.append(show("Manifest Freeze", manifest.get("status") == "frozen" and manifest.get("backward_compatible") is True))
    checks.append(show("Baseline Version", baseline.get("version") == "1.0-beta-cli-v1"))

    regression = run_cli_regression_suite()
    checks.append(show("Regression Suite", all(regression.values())))

    acceptance = run_cli_acceptance()
    checks.append(show("Acceptance CLI", acceptance.ok))
    checks.append(show("Packaging Compatible", "plugin" in registry_names and "config" in registry_names))
    checks.append(show("Backward Compatible", baseline.get("backward_compatible") is True and manifest.get("backward_compatible") is True))

    if all(checks):
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
