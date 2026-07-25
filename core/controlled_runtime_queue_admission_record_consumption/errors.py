"""Stage 6.13 queue-admission record consumption errors."""


class QueueAdmissionRecordConsumptionError(Exception):
    pass


class QueueAdmissionRecordConsumptionPathError(QueueAdmissionRecordConsumptionError):
    pass


class QueueAdmissionRecordConsumptionSchemaError(QueueAdmissionRecordConsumptionError):
    pass


class QueueAdmissionRecordConsumptionIntegrityError(QueueAdmissionRecordConsumptionError):
    pass


class QueueAdmissionRecordAlreadyConsumedError(QueueAdmissionRecordConsumptionError):
    pass


class QueueAdmissionRecordConsumptionConflictError(QueueAdmissionRecordConsumptionError):
    pass


class QueueAdmissionRecordConsumptionCommitError(QueueAdmissionRecordConsumptionError):
    pass


class QueueAdmissionRecordConsumptionVerificationError(QueueAdmissionRecordConsumptionError):
    pass