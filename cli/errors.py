from __future__ import annotations


class CLIError(Exception):
    """Base exception for NTPE CLI failures."""

    exit_code = 1


class CommandNotFoundError(CLIError):
    exit_code = 2


class CommandExecutionError(CLIError):
    exit_code = 3
