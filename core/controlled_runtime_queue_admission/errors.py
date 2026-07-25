"""Dedicated Stage 7.1 controlled queue-admission errors."""


class ControlledRuntimeQueueAdmissionError(Exception):
    """Base error for the Stage 7.1 boundary."""


class ControlledRuntimeQueueAdmissionPathError(
    ControlledRuntimeQueueAdmissionError
):
    pass


class ControlledRuntimeQueueAdmissionSchemaError(
    ControlledRuntimeQueueAdmissionError
):
    pass


class ControlledRuntimeQueueAdmissionIntegrityError(
    ControlledRuntimeQueueAdmissionError
):
    pass


class ControlledRuntimeQueueAdmissionPolicyError(
    ControlledRuntimeQueueAdmissionError
):
    def __init__(self, reason_codes: tuple[str, ...]):
        self.reason_codes = tuple(reason_codes)
        super().__init__(",".join(self.reason_codes))


class ControlledRuntimeQueueAlreadyAdmittedError(
    ControlledRuntimeQueueAdmissionError
):
    pass


class ControlledRuntimeQueueAdmissionConflictError(
    ControlledRuntimeQueueAdmissionError
):
    pass


class ControlledRuntimeQueueAdmissionCommitError(
    ControlledRuntimeQueueAdmissionError
):
    pass


class ControlledRuntimeQueueAdmissionVerificationError(
    ControlledRuntimeQueueAdmissionError
):
    pass
