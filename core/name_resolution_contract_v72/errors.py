class NameResolutionError(ValueError):
    """Base error for deterministic offline name resolution."""


class ConflictingTargetMappingError(NameResolutionError):
    """Raised when authoritative sources disagree on an approved target name."""


class InvalidTargetMappingError(NameResolutionError):
    """Raised when a target mapping violates eligibility constraints."""
