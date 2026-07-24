"""Stage 6.10 controlled queue-admission authorization."""

from .authorizer import ControlledRuntimeQueueAdmissionAuthorizer
from .errors import (
    QueueAdmissionAuthorizationError,
    QueueAdmissionAuthorizationRequestError,
    QueueAdmissionAuthorizationUpstreamError,
    QueueAdmissionAuthorizationVerificationError,
)
from .models import (
    ControlledRuntimeQueueAdmissionAuthorizationDecision,
    ControlledRuntimeQueueAdmissionAuthorizationRequest,
    ControlledRuntimeQueueAdmissionAuthorizationResult,
    ControlledRuntimeQueueAdmissionAuthorizationVerificationResult,
)
from .policy import ControlledRuntimeQueueAdmissionAuthorizationPolicy
from .verification import verify_controlled_runtime_queue_admission_authorization

__all__ = [
    "ControlledRuntimeQueueAdmissionAuthorizationRequest",
    "ControlledRuntimeQueueAdmissionAuthorizationDecision",
    "ControlledRuntimeQueueAdmissionAuthorizationResult",
    "ControlledRuntimeQueueAdmissionAuthorizationVerificationResult",
    "ControlledRuntimeQueueAdmissionAuthorizationPolicy",
    "ControlledRuntimeQueueAdmissionAuthorizer",
    "verify_controlled_runtime_queue_admission_authorization",
    "QueueAdmissionAuthorizationError",
    "QueueAdmissionAuthorizationRequestError",
    "QueueAdmissionAuthorizationUpstreamError",
    "QueueAdmissionAuthorizationVerificationError",
]
