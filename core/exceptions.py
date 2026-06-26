class NTPEError(Exception):
    """NTPE base exception."""


class ConfigError(NTPEError):
    """Configuration loading or validation failed."""


class EngineError(NTPEError):
    """AI engine related error."""


class ValidationError(NTPEError):
    """Translation validation failed."""
