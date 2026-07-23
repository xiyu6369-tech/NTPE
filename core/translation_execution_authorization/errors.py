from __future__ import annotations


class TranslationExecutionAuthorizationError(ValueError):
    """Base error for deterministic execution authorization evaluation."""


class InvalidExecutionAuthorizationInputError(
    TranslationExecutionAuthorizationError
):
    """Raised when an evaluator input has the wrong public type."""


class InvalidExecutionPackageStateError(TranslationExecutionAuthorizationError):
    """Raised when a package state is not eligible for authorization review."""

    def __init__(self, message: str, *, finding: object | None = None) -> None:
        super().__init__(message)
        self.finding = finding


class ExecutionAuthorizationConsistencyError(
    TranslationExecutionAuthorizationError
):
    """Raised when package data is inconsistent or has been tampered with."""

    def __init__(self, message: str, *, finding: object | None = None) -> None:
        super().__init__(message)
        self.finding = finding


class ExecutionAuthorizationPolicyError(TranslationExecutionAuthorizationError):
    """Raised when an injected policy attempts to relax the safety boundary."""

    def __init__(self, message: str, *, finding: object | None = None) -> None:
        super().__init__(message)
        self.finding = finding

