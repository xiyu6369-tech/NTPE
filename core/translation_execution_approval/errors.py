from __future__ import annotations


class TranslationExecutionApprovalError(ValueError):
    """Base error for explicit human execution approval."""


class InvalidExecutionApprovalInputError(TranslationExecutionApprovalError):
    """Raised when an approval API input has the wrong public type."""


class InvalidHumanApprovalRequestError(TranslationExecutionApprovalError):
    """Raised when explicit approval evidence is absent or incomplete."""

    def __init__(self, message: str, *, finding: object | None = None) -> None:
        super().__init__(message)
        self.finding = finding


class ExecutionApprovalConsistencyError(TranslationExecutionApprovalError):
    """Raised when package and authorization evidence are inconsistent."""

    def __init__(self, message: str, *, finding: object | None = None) -> None:
        super().__init__(message)
        self.finding = finding


class ExecutionApprovalScopeError(TranslationExecutionApprovalError):
    """Raised when the requested unit scope is invalid."""

    def __init__(self, message: str, *, finding: object | None = None) -> None:
        super().__init__(message)
        self.finding = finding


class ExecutionApprovalPolicyError(TranslationExecutionApprovalError):
    """Raised when a request attempts to authorize a prohibited capability."""

    def __init__(self, message: str, *, finding: object | None = None) -> None:
        super().__init__(message)
        self.finding = finding
