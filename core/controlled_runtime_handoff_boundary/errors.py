"""Stage 6.5 specific errors."""


class ControlledRuntimeHandoffError(RuntimeError):
    """Base handoff error."""


class ControlledRuntimeHandoffVerificationError(ControlledRuntimeHandoffError):
    """Raised when a handoff receipt does not verify."""
