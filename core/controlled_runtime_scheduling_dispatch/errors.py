"""Dedicated Stage 7.2 controlled scheduling errors."""


class ControlledRuntimeSchedulingDispatchError(Exception):
    """Base class for Stage 7.2 failures."""


class ControlledRuntimeSchedulingDispatchPathError(
    ControlledRuntimeSchedulingDispatchError
):
    pass


class ControlledRuntimeSchedulingDispatchSchemaError(
    ControlledRuntimeSchedulingDispatchError
):
    pass


class ControlledRuntimeSchedulingDispatchIntegrityError(
    ControlledRuntimeSchedulingDispatchError
):
    pass


class ControlledRuntimeSchedulingDispatchPolicyError(
    ControlledRuntimeSchedulingDispatchError
):
    def __init__(self, reason_codes: tuple[str, ...]):
        self.reason_codes = tuple(reason_codes)
        super().__init__(",".join(self.reason_codes))


class ControlledRuntimeAlreadyScheduledError(
    ControlledRuntimeSchedulingDispatchError
):
    pass


class ControlledRuntimeSchedulingConflictError(
    ControlledRuntimeSchedulingDispatchError
):
    pass


class ControlledRuntimeSchedulingCommitError(
    ControlledRuntimeSchedulingDispatchError
):
    pass


class ControlledRuntimeSchedulingDispatchVerificationError(
    ControlledRuntimeSchedulingDispatchError
):
    pass
