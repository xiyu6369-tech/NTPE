"""Dedicated Stage 7.3 controlled translation errors."""


class ControlledTranslationRuntimeError(Exception):
    pass


class ControlledTranslationDispatchVerificationError(ControlledTranslationRuntimeError):
    pass


class ControlledTranslationResolutionError(ControlledTranslationRuntimeError):
    pass


class ControlledTranslationSourceIntegrityError(ControlledTranslationRuntimeError):
    pass


class ControlledTranslationMultipleChunkError(ControlledTranslationRuntimeError):
    pass


class ControlledTranslationProviderConfigurationError(ControlledTranslationRuntimeError):
    pass


class ControlledTranslationProviderTimeoutError(ControlledTranslationRuntimeError):
    pass


class ControlledTranslationProviderRequestError(ControlledTranslationRuntimeError):
    pass


class ControlledTranslationProviderResponseError(ControlledTranslationRuntimeError):
    pass


class ControlledTranslationQualityError(ControlledTranslationRuntimeError):
    pass


class ControlledTranslationOutputError(ControlledTranslationRuntimeError):
    pass


class ControlledTranslationVerificationError(ControlledTranslationRuntimeError):
    pass
