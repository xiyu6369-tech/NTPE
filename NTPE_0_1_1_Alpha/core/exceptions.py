"""Custom exceptions used by NTPE."""

from __future__ import annotations


class NTPEError(Exception):
    """Base exception for NTPE."""


class ConfigError(NTPEError):
    """Raised when configuration cannot be loaded or validated."""


class SchedulerError(NTPEError):
    """Raised when scheduler state is invalid."""


class EngineError(NTPEError):
    """Raised when a translation engine fails."""
