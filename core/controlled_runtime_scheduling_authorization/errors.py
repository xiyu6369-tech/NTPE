"""Stage 6.6 fail-closed errors."""


class ControlledRuntimeSchedulingAuthorizationError(RuntimeError):
    """Base Stage 6.6 error."""


class ControlledRuntimeSchedulingAuthorizationVerificationError(
    ControlledRuntimeSchedulingAuthorizationError
):
    """Raised when a scheduling authorization decision does not verify."""
