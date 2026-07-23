from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import RuntimeSubmissionFinding


class ControlledRuntimeSubmissionError(ValueError):
    """Base error for controlled runtime submission preparation."""

    def __init__(
        self,
        message: str,
        *,
        finding: RuntimeSubmissionFinding | None = None,
    ) -> None:
        super().__init__(message)
        self.finding = finding


class InvalidRuntimeSubmissionInputError(ControlledRuntimeSubmissionError):
    """Raised when an input has the wrong public API type."""


class RuntimeSubmissionConsistencyError(ControlledRuntimeSubmissionError):
    """Raised when the Stage 4 fingerprint or content chain is inconsistent."""


class RuntimeSubmissionScopeError(ControlledRuntimeSubmissionError):
    """Raised when an approval scope is invalid or cannot be mapped exactly."""


class RuntimeSubmissionPolicyError(ControlledRuntimeSubmissionError):
    """Raised when an approval attempts to relax a prohibited policy."""


class RuntimeSubmissionInvariantError(RuntimeSubmissionConsistencyError):
    """Raised when a materialized submission violates an internal invariant."""
