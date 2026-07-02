"""Stage-07.5 SDK Error Handling API error codes.

The code list is additive: existing SDK response objects still expose their
legacy string `errors` fields, while SDKErrorCode provides a stable typed layer
for integrations that need predictable error handling.
"""
from __future__ import annotations

from enum import Enum


SDK_ERROR_STAGE = "NTPE 1.0 Beta Stage-07.5 SDK Error Handling API"
SDK_ERROR_VERSION = "0.7.5"


class SDKErrorCode(str, Enum):
    """Stable SDK error code namespace."""

    UNKNOWN = "sdk.unknown"
    VALIDATION = "sdk.validation"
    CONFIGURATION = "sdk.configuration"
    SESSION = "sdk.session"
    TRANSLATION = "sdk.translation"
    BATCH = "sdk.batch"
    STREAMING = "sdk.streaming"
    RUNTIME = "sdk.runtime"
    PROVIDER = "sdk.provider"
    TIMEOUT = "sdk.timeout"
    CANCELLED = "sdk.cancelled"
    IO = "sdk.io"

    @classmethod
    def coerce(cls, value: "SDKErrorCode | str | None") -> "SDKErrorCode":
        if isinstance(value, cls):
            return value
        if value is None:
            return cls.UNKNOWN
        try:
            return cls(str(value))
        except ValueError:
            normalized = str(value).lower().strip()
            for item in cls:
                if item.name.lower() == normalized:
                    return item
            return cls.UNKNOWN
