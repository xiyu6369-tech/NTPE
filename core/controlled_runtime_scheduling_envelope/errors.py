"""Stage 6.8 controlled Runtime scheduling-envelope errors."""


class ControlledRuntimeSchedulingEnvelopeError(Exception):
    """Base Stage 6.8 error."""


class ControlledRuntimeSchedulingEnvelopeVerificationError(
    ControlledRuntimeSchedulingEnvelopeError
):
    """The scheduling envelope failed deterministic verification."""
