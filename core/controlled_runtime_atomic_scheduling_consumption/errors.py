"""Stage 6.7 atomic scheduling authorization consumption error taxonomy."""


class AtomicSchedulingConsumptionError(Exception):
    """Base error for the atomic scheduling-consumption boundary."""


class AtomicSchedulingConsumptionRequestError(AtomicSchedulingConsumptionError):
    """The scheduling-consumption request is invalid."""


class AtomicSchedulingConsumptionUpstreamError(AtomicSchedulingConsumptionError):
    """An authenticated upstream contract is ineligible or inconsistent."""


class AtomicSchedulingConsumptionRegistryPathError(AtomicSchedulingConsumptionError):
    """The explicitly supplied registry path is unsafe or outside allowed_root."""


class AtomicSchedulingConsumptionRegistrySchemaError(AtomicSchedulingConsumptionError):
    """The registry schema is missing, malformed, or incompatible."""


class AtomicSchedulingConsumptionRegistryIntegrityError(AtomicSchedulingConsumptionError):
    """A durable registry row failed integrity validation."""


class AtomicSchedulingConsumptionAlreadyConsumedError(AtomicSchedulingConsumptionError):
    """The scheduling authorization already has a durable scheduling-consumption claim."""


class AtomicSchedulingConsumptionCommitError(AtomicSchedulingConsumptionError):
    """The atomic scheduling-consumption claim transaction did not commit."""


class AtomicSchedulingConsumptionVerificationError(AtomicSchedulingConsumptionError):
    """An atomic scheduling-consumption claim failed canonical or binding verification."""