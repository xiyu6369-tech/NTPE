"""Stage 6.9 controlled scheduling-envelope consumption errors."""


class SchedulingEnvelopeConsumptionError(Exception):
    """Base Stage 6.9 error."""


class SchedulingEnvelopeConsumptionRequestError(SchedulingEnvelopeConsumptionError):
    """The consumption request is invalid."""


class SchedulingEnvelopeConsumptionUpstreamError(SchedulingEnvelopeConsumptionError):
    """The authenticated upstream chain is invalid."""


class SchedulingEnvelopeConsumptionRegistryPathError(
    SchedulingEnvelopeConsumptionError
):
    """The registry path is unsafe."""


class SchedulingEnvelopeConsumptionRegistrySchemaError(
    SchedulingEnvelopeConsumptionError
):
    """The registry schema is malformed."""


class SchedulingEnvelopeConsumptionRegistryIntegrityError(
    SchedulingEnvelopeConsumptionError
):
    """A durable row failed canonical integrity checks."""


class SchedulingEnvelopeAlreadyConsumedError(SchedulingEnvelopeConsumptionError):
    """The scheduling envelope already has a durable claim."""


class SchedulingEnvelopeConsumptionConflictError(SchedulingEnvelopeConsumptionError):
    """A request or claim identity conflicts with durable state."""


class SchedulingEnvelopeConsumptionCommitError(SchedulingEnvelopeConsumptionError):
    """The atomic transaction failed."""


class SchedulingEnvelopeConsumptionVerificationError(
    SchedulingEnvelopeConsumptionError
):
    """A Stage 6.9 claim failed verification."""
