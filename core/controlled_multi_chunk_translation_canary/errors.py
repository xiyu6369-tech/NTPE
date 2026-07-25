"""Dedicated fail-closed Stage 7.4 errors."""


class ControlledMultiChunkError(Exception):
    pass


class ControlledMultiChunkAuthorityError(ControlledMultiChunkError):
    pass


class ControlledMultiChunkResolutionError(ControlledMultiChunkError):
    pass


class ControlledMultiChunkProviderError(ControlledMultiChunkError):
    pass


class ControlledMultiChunkQualityError(ControlledMultiChunkError):
    pass


class ControlledMultiChunkCheckpointError(ControlledMultiChunkError):
    pass


class ControlledMultiChunkOutputError(ControlledMultiChunkError):
    pass


class ControlledMultiChunkVerificationError(ControlledMultiChunkError):
    pass
