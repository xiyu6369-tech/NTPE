from __future__ import annotations


class TranslationExecutionPackageError(ValueError):
    """Base error for deterministic offline execution package creation."""


class InvalidExecutionPackageInputError(TranslationExecutionPackageError):
    """Raised when the builder receives anything but BookPreparationResult."""


class InvalidPreparationStateError(TranslationExecutionPackageError):
    """Raised when preparation has not reached an accepted ready state."""

    def __init__(
        self,
        message: str,
        *,
        preparation_status: str,
        action: str,
        finding_codes: tuple[str, ...],
    ) -> None:
        super().__init__(message)
        self.preparation_status = preparation_status
        self.action = action
        self.finding_codes = finding_codes


class ExecutionPackageConsistencyError(TranslationExecutionPackageError):
    """Raised when a completed preparation result is internally inconsistent."""

    def __init__(self, message: str, *, finding: object | None = None) -> None:
        super().__init__(message)
        self.finding = finding


class ExecutionPackageInvariantError(TranslationExecutionPackageError):
    """Raised when a materialized package violates its immutable contract."""

