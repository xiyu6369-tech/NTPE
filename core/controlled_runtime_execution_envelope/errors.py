"""Stage 6.4 — Controlled Runtime Execution Envelope Errors

Deterministic, bounded, immutable error types.
No stack traces, no machine identifiers, no timestamps.
"""

from __future__ import annotations


class ControlledRuntimeExecutionEnvelopeError(Exception):
    """Base error for Controlled Runtime Execution Envelope operations.

    All subclasses carry a canonical `code` for deterministic
    policy-driven handling.
    """

    def __init__(self, message: str, *, code: str = "ENVELOPE_ERROR") -> None:
        super().__init__(message)
        self.code = code


class InvalidControlledRuntimeExecutionEnvelopeInputError(
    ControlledRuntimeExecutionEnvelopeError
):
    """Input validation failure — incorrect types, missing fields, malformed values."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "INVALID_ENVELOPE_INPUT",
    ) -> None:
        super().__init__(message, code=code)


class ControlledRuntimeExecutionEnvelopeBuildError(
    ControlledRuntimeExecutionEnvelopeError
):
    """Builder failure — envelope could not satisfy all success conditions."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "ENVELOPE_BUILD_FAILED",
    ) -> None:
        super().__init__(message, code=code)


class ControlledRuntimeExecutionEnvelopeVerificationError(
    ControlledRuntimeExecutionEnvelopeError
):
    """Verification failure — envelope integrity or binding violated."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "ENVELOPE_VERIFICATION_FAILED",
    ) -> None:
        super().__init__(message, code=code)


class ControlledRuntimeExecutionEnvelopePolicyError(
    ControlledRuntimeExecutionEnvelopeError
):
    """Policy violation — attempt to relax or deviate from Stage 6.4 boundary."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "ENVELOPE_POLICY_VIOLATION",
    ) -> None:
        super().__init__(message, code=code)