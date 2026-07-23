from __future__ import annotations


class ControlledRuntimeAuthorizationConsumptionError(RuntimeError):
    """Base error for Stage 6.2 consumption preparation failures."""


class InvalidConsumptionRequestError(ControlledRuntimeAuthorizationConsumptionError):
    """Raised when a consumption request cannot be represented safely."""


class AuthorizationNotEligibleError(ControlledRuntimeAuthorizationConsumptionError):
    """Raised when the referenced authorization is not eligible for consumption."""


class UpstreamContractMismatchError(ControlledRuntimeAuthorizationConsumptionError):
    """Raised when upstream frozen contracts do not match expected fingerprints."""


class AlreadyConsumedError(ControlledRuntimeAuthorizationConsumptionError):
    """Raised when the authorization has already been consumed."""


class ConsumptionVerificationError(ControlledRuntimeAuthorizationConsumptionError):
    """Raised when a consumption record fails verification."""