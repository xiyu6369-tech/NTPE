"""Stage 6.13 controlled queue-admission record consumption."""

from .consumer import ControlledRuntimeQueueAdmissionRecordConsumer
from .errors import (
    QueueAdmissionRecordAlreadyConsumedError,
    QueueAdmissionRecordConsumptionCommitError,
    QueueAdmissionRecordConsumptionConflictError,
    QueueAdmissionRecordConsumptionError,
    QueueAdmissionRecordConsumptionIntegrityError,
    QueueAdmissionRecordConsumptionPathError,
    QueueAdmissionRecordConsumptionSchemaError,
    QueueAdmissionRecordConsumptionVerificationError,
)
from .models import (
    ControlledRuntimeQueueAdmissionRecordConsumptionClaim,
    ControlledRuntimeQueueAdmissionRecordConsumptionRequest,
    ControlledRuntimeQueueAdmissionRecordConsumptionResult,
    ControlledRuntimeQueueAdmissionRecordConsumptionVerificationResult,
)
from .policy import ControlledRuntimeQueueAdmissionRecordConsumptionPolicy
from .registry import ControlledRuntimeQueueAdmissionRecordConsumptionRegistry
from .verification import (
    verify_controlled_runtime_queue_admission_record_consumption,
)

__all__ = [
    "ControlledRuntimeQueueAdmissionRecordConsumptionRequest",
    "ControlledRuntimeQueueAdmissionRecordConsumptionClaim",
    "ControlledRuntimeQueueAdmissionRecordConsumptionResult",
    "ControlledRuntimeQueueAdmissionRecordConsumptionVerificationResult",
    "ControlledRuntimeQueueAdmissionRecordConsumptionPolicy",
    "ControlledRuntimeQueueAdmissionRecordConsumptionRegistry",
    "ControlledRuntimeQueueAdmissionRecordConsumer",
    "verify_controlled_runtime_queue_admission_record_consumption",
    "QueueAdmissionRecordConsumptionError",
    "QueueAdmissionRecordConsumptionPathError",
    "QueueAdmissionRecordConsumptionSchemaError",
    "QueueAdmissionRecordConsumptionIntegrityError",
    "QueueAdmissionRecordAlreadyConsumedError",
    "QueueAdmissionRecordConsumptionConflictError",
    "QueueAdmissionRecordConsumptionCommitError",
    "QueueAdmissionRecordConsumptionVerificationError",
]