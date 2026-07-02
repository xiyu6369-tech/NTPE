from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .compatibility import check_cli_compatibility
from .regression import run_cli_regression_suite


@dataclass
class CLIAcceptanceResult:
    ok: bool
    compatibility: bool
    regression: bool
    checks: Dict[str, bool]

    def to_dict(self) -> Dict[str, object]:
        return {
            "ok": self.ok,
            "compatibility": self.compatibility,
            "regression": self.regression,
            "checks": dict(self.checks),
        }


def run_cli_acceptance() -> CLIAcceptanceResult:
    compatibility = check_cli_compatibility()
    regression_checks = run_cli_regression_suite()
    regression_ok = all(regression_checks.values())
    return CLIAcceptanceResult(
        ok=compatibility.ok and regression_ok,
        compatibility=compatibility.ok,
        regression=regression_ok,
        checks={**compatibility.checks, **regression_checks},
    )
