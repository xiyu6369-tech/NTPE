from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.book_intake import BookIntakeResult, BookPreflightResult


class BookPreparationError(ValueError):
    """Base error for deterministic book preparation."""


class InvalidBookPreparationInputError(BookPreparationError):
    """Raised when a public preparation API receives an invalid input."""


class BookPreparationConsistencyError(BookPreparationError):
    """Raised when completed stages describe inconsistent source data."""

    def __init__(self, message: str, *, finding: object | None = None) -> None:
        super().__init__(message)
        self.finding = finding


class BookPreparationBlockedError(BookPreparationError):
    """Fail-fast error preserving upstream evidence for a blocked pipeline."""

    def __init__(
        self,
        message: str,
        *,
        intake_result: BookIntakeResult,
        preflight_result: BookPreflightResult | None = None,
        finding: object | None = None,
    ) -> None:
        super().__init__(message)
        self.intake_result = intake_result
        self.preflight_result = preflight_result
        self.finding = finding


class BookPreparationStageError(BookPreparationError):
    """Wrap an injected downstream dependency failure with exception chaining."""

    def __init__(self, stage: str, *, finding: object | None = None) -> None:
        super().__init__(f"Book preparation stage failed: {stage}.")
        self.stage = stage
        self.finding = finding
