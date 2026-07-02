from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from cli.main import build_registry
from cli.manifest import build_cli_manifest
from cli.parser import build_parser
from cli.result import CLIResult

from .baseline import STABLE_JSON_KEYS, build_cli_baseline
from .manifest import build_cli_freeze_manifest


@dataclass
class CompatibilityReport:
    ok: bool
    checks: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "checks": dict(self.checks),
            "errors": list(self.errors),
            "data": dict(self.data),
        }


class CLICompatibilityChecker:
    """Validate the public CLI v1 surface without changing existing commands."""

    def __init__(self) -> None:
        self.baseline = build_cli_baseline()

    def check_registry(self) -> bool:
        registry = build_registry()
        names = registry.names()
        return all(command in names for command in self.baseline["commands"])

    def check_manifest(self) -> bool:
        manifest = build_cli_manifest()
        commands = manifest.get("commands", [])
        return all(command in commands for command in self.baseline["commands"])

    def check_json_schema(self) -> bool:
        result = CLIResult.success("schema check", sample=True)
        keys = sorted(result.to_dict().keys())
        return keys == sorted(STABLE_JSON_KEYS)

    def check_help_output(self) -> bool:
        help_text = build_parser().format_help()
        return all(command in help_text for command in ["version", "doctor", "translate", "project", "benchmark", "quality", "session", "config", "plugin"])

    def check_freeze_manifest(self) -> bool:
        manifest = build_cli_freeze_manifest()
        return manifest.get("status") == "frozen" and manifest.get("backward_compatible") is True

    def run(self) -> CompatibilityReport:
        checks = {
            "command_registry": self.check_registry(),
            "cli_manifest": self.check_manifest(),
            "json_schema": self.check_json_schema(),
            "help_output": self.check_help_output(),
            "freeze_manifest": self.check_freeze_manifest(),
        }
        errors = [name for name, passed in checks.items() if not passed]
        return CompatibilityReport(
            ok=not errors,
            checks=checks,
            errors=errors,
            data={
                "baseline": self.baseline,
                "freeze_manifest": build_cli_freeze_manifest(),
            },
        )


def check_cli_compatibility() -> CompatibilityReport:
    return CLICompatibilityChecker().run()
