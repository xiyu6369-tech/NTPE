class ControlledRuntimeExecutionAuthorizationError(RuntimeError):
    """Base error for malformed Stage 6.1 authorization inputs."""


class InvalidControlledRuntimeExecutionAuthorizationInputError(
    ControlledRuntimeExecutionAuthorizationError
):
    """Raised when the authorizer cannot represent an input safely."""

