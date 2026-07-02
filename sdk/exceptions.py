"""Public SDK exceptions for NTPE SDK integrations."""
from __future__ import annotations


class SDKError(Exception):
    """Base exception for public SDK errors."""


class SDKSessionError(SDKError):
    """Raised when an SDK session operation is invalid."""
