"""Stage 6.3 fail-closed error taxonomy."""


class AtomicAuthorizationConsumptionError(Exception):
    """Base error for the atomic consumption boundary."""


class AtomicConsumptionRequestError(AtomicAuthorizationConsumptionError):
    """The claim request is invalid."""


class AtomicConsumptionUpstreamError(AtomicAuthorizationConsumptionError):
    """An authenticated upstream contract is ineligible or inconsistent."""


class AtomicConsumptionRegistryPathError(AtomicAuthorizationConsumptionError):
    """The explicitly supplied registry path is unsafe."""


class AtomicConsumptionRegistrySchemaError(AtomicAuthorizationConsumptionError):
    """The registry schema is missing, malformed, or incompatible."""


class AtomicConsumptionRegistryIntegrityError(AtomicAuthorizationConsumptionError):
    """A durable registry row failed integrity validation."""


class AtomicConsumptionAlreadyConsumedError(AtomicAuthorizationConsumptionError):
    """The authorization already has a durable claim."""


class AtomicConsumptionCommitError(AtomicAuthorizationConsumptionError):
    """The atomic claim transaction did not commit."""


class AtomicConsumptionVerificationError(AtomicAuthorizationConsumptionError):
    """A claim failed canonical or binding verification."""
