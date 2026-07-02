"""Public SDK exceptions for NTPE SDK integrations.

Stage-07.5 keeps the original SDKError/SDKSessionError names and adds typed
error handling classes by re-exporting the new additive error API.
"""
from __future__ import annotations

from .errors import (
    SDKException,
    SDKValidationError,
    SDKConfigurationError,
    SDKTranslationError,
    SDKBatchError,
    SDKStreamingError,
    SDKRuntimeBridgeError,
)


class SDKError(SDKException):
    """Base exception for public SDK errors.

    Kept for Stage-07.0 backward compatibility.
    """


class SDKSessionError(SDKError):
    """Raised when an SDK session operation is invalid."""
