from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ControlledRuntimeExecutionFinding


class ControlledRuntimeExecutionPlanError(ValueError):
    """Base error for controlled runtime execution plan preparation."""

    def __init__(
        self,
        message: str,
        *,
        finding: ControlledRuntimeExecutionFinding | None = None,
    ) -> None:
        super().__init__(message)
        self.finding = finding


class InvalidControlledRuntimeExecutionInputError(
    ControlledRuntimeExecutionPlanError
):
    """Raised when a planner input has an invalid public API type."""


class ControlledRuntimeExecutionConsistencyError(
    ControlledRuntimeExecutionPlanError
):
    """Raised when the adapter preparation chain is noncanonical."""


class ControlledRuntimeExecutionScopeError(ControlledRuntimeExecutionPlanError):
    """Raised when the caller does not select exactly one approved unit."""


class ControlledRuntimeExecutionPolicyError(ControlledRuntimeExecutionPlanError):
    """Raised when an execution policy relaxes or cannot satisfy the boundary."""


class ControlledRuntimeExecutionInvariantError(
    ControlledRuntimeExecutionConsistencyError
):
    """Raised when a materialized plan violates an internal invariant."""
