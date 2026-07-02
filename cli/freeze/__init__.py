from .baseline import build_cli_baseline, command_is_stable, expected_commands
from .compatibility import CLICompatibilityChecker, CompatibilityReport, check_cli_compatibility
from .manifest import build_cli_freeze_manifest, attach_cli_freeze_manifest
from .regression import CLIRegressionSuite, run_cli_regression_suite
from .acceptance import CLIAcceptanceResult, run_cli_acceptance

__all__ = [
    "build_cli_baseline",
    "command_is_stable",
    "expected_commands",
    "CLICompatibilityChecker",
    "CompatibilityReport",
    "check_cli_compatibility",
    "build_cli_freeze_manifest",
    "attach_cli_freeze_manifest",
    "CLIRegressionSuite",
    "run_cli_regression_suite",
    "CLIAcceptanceResult",
    "run_cli_acceptance",
]
