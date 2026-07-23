from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import RuntimeAdapterFinding


class ControlledRuntimeAdapterError(ValueError):
    """Base error for offline controlled runtime adapter preparation."""

    def __init__(
        self,
        message: str,
        *,
        finding: RuntimeAdapterFinding | None = None,
    ) -> None:
        super().__init__(message)
        self.finding = finding


class InvalidRuntimeAdapterInputError(ControlledRuntimeAdapterError):
    """Raised when a public API input has an invalid type."""


class RuntimeAdapterConsistencyError(ControlledRuntimeAdapterError):
    """Raised when a submission package is inconsistent or noncanonical."""


class RuntimeAdapterCapabilityError(ControlledRuntimeAdapterError):
    """Raised when a capability profile relaxes the offline boundary."""


class RuntimeAdapterPolicyError(ControlledRuntimeAdapterError):
    """Raised when the adapter policy is invalid or relaxed."""


class RuntimeAdapterInvariantError(RuntimeAdapterConsistencyError):
    """Raised when a materialized adapter contract violates an invariant."""
