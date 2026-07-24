"""Stage 6.10 queue-admission authorization errors."""


class QueueAdmissionAuthorizationError(Exception):
    """Base Stage 6.10 error."""


class QueueAdmissionAuthorizationRequestError(QueueAdmissionAuthorizationError):
    """The authorization request is invalid."""


class QueueAdmissionAuthorizationUpstreamError(QueueAdmissionAuthorizationError):
    """The authenticated upstream authority is invalid."""


class QueueAdmissionAuthorizationVerificationError(
    QueueAdmissionAuthorizationError
):
    """The authorization decision failed verification."""
