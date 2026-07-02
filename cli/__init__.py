from __future__ import annotations

from .context import CLIContext
from .result import CLIResult
from .command import CLICommand, CommandRegistry
from .manifest import build_cli_manifest, attach_cli_manifest
from .main import main, run_cli

__all__ = [
    "CLIContext",
    "CLIResult",
    "CLICommand",
    "CommandRegistry",
    "build_cli_manifest",
    "attach_cli_manifest",
    "main",
    "run_cli",
]
