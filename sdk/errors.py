"""Stage-07.5 SDK Error Handling API.

This module adds typed exceptions, serializable error records, and response
normalizers while preserving existing Stage-07.0 through Stage-07.4 behavior.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .error_codes import SDKErrorCode, SDK_ERROR_STAGE, SDK_ERROR_VERSION
from .error_models import SDKErrorContext, SDKErrorRecord
from .error_response import SDKErrorResponse


class SDKException(Exception):
    """Base typed SDK exception with a stable SDKErrorRecord payload."""

    default_code = SDKErrorCode.UNKNOWN
    component = "sdk"

    def __init__(
        self,
        message: str,
        *,
        code: SDKErrorCode | str | None = None,
        job_id: str = "sdk-job",
        session_id: Optional[str] = None,
        operation: str = "unknown",
        retryable: bool = False,
        cause: Optional[BaseException | str] = None,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = str(message)
        self.code = SDKErrorCode.coerce(code or self.default_code)
        self.cause = cause
        self.context = SDKErrorContext(
            stage=SDK_ERROR_STAGE,
            version=SDK_ERROR_VERSION,
            job_id=job_id,
            session_id=session_id,
            component=self.component,
            operation=operation,
            retryable=retryable,
            metadata=dict(metadata or {}),
        )
        self.details = dict(details or {})

    def to_error_record(self) -> SDKErrorRecord:
        return SDKErrorRecord(
            code=self.code,
            message=self.message,
            context=self.context,
            cause=str(self.cause) if self.cause else None,
            details=dict(self.details),
        )

    def to_response(self) -> SDKErrorResponse:
        return SDKErrorResponse.from_error(self.to_error_record())

    def to_dict(self) -> Dict[str, Any]:
        return self.to_error_record().to_dict()


class SDKValidationError(SDKException):
    default_code = SDKErrorCode.VALIDATION
    component = "sdk.validation"


class SDKConfigurationError(SDKException):
    default_code = SDKErrorCode.CONFIGURATION
    component = "sdk.configuration"


class SDKTranslationError(SDKException):
    default_code = SDKErrorCode.TRANSLATION
    component = "sdk.translation"


class SDKBatchError(SDKException):
    default_code = SDKErrorCode.BATCH
    component = "sdk.batch"


class SDKStreamingError(SDKException):
    default_code = SDKErrorCode.STREAMING
    component = "sdk.streaming"


class SDKRuntimeBridgeError(SDKException):
    default_code = SDKErrorCode.RUNTIME
    component = "sdk.runtime_bridge"


def normalize_exception(
    exc: BaseException,
    *,
    code: SDKErrorCode | str | None = None,
    job_id: str = "sdk-job",
    session_id: Optional[str] = None,
    component: str = "sdk",
    operation: str = "unknown",
    retryable: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
) -> SDKErrorRecord:
    """Convert any exception into a serializable SDKErrorRecord."""

    if isinstance(exc, SDKException):
        return exc.to_error_record()
    return SDKErrorRecord(
        code=SDKErrorCode.coerce(code),
        message=str(exc) or exc.__class__.__name__,
        context=SDKErrorContext(
            job_id=job_id,
            session_id=session_id,
            component=component,
            operation=operation,
            retryable=retryable,
            metadata=dict(metadata or {}),
        ),
        cause=exc.__class__.__name__,
    )


def error_response(
    message: str,
    *,
    code: SDKErrorCode | str | None = None,
    job_id: str = "sdk-job",
    session_id: Optional[str] = None,
    component: str = "sdk",
    operation: str = "unknown",
    retryable: bool = False,
    data: Optional[Dict[str, Any]] = None,
) -> SDKErrorResponse:
    record = SDKErrorRecord(
        code=SDKErrorCode.coerce(code),
        message=str(message),
        context=SDKErrorContext(
            job_id=job_id,
            session_id=session_id,
            component=component,
            operation=operation,
            retryable=retryable,
        ),
    )
    return SDKErrorResponse.from_error(record, data=data)


def normalize_response_errors(response: Any, *, fallback_code: SDKErrorCode | str | None = None) -> list[SDKErrorRecord]:
    """Read legacy `.errors` fields and expose Stage-07.5 structured records."""

    errors = getattr(response, "errors", []) or []
    job_id = getattr(response, "job_id", "sdk-job")
    session_id = getattr(response, "session_id", None)
    records: list[SDKErrorRecord] = []
    for item in errors:
        if isinstance(item, SDKErrorRecord):
            records.append(item)
        elif isinstance(item, dict):
            records.append(SDKErrorRecord.from_dict(item))
        else:
            records.append(
                SDKErrorRecord(
                    code=SDKErrorCode.coerce(fallback_code),
                    message=str(item),
                    context=SDKErrorContext(job_id=job_id, session_id=session_id),
                )
            )
    return records


def build_sdk_error_manifest(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": "NTPE SDK Error Handling API",
        "stage": SDK_ERROR_STAGE,
        "version": SDK_ERROR_VERSION,
        "status": "beta",
        "components": [
            "SDKErrorCode",
            "SDKException",
            "SDKValidationError",
            "SDKTranslationError",
            "SDKBatchError",
            "SDKStreamingError",
            "SDKRuntimeBridgeError",
            "SDKErrorContext",
            "SDKErrorRecord",
            "SDKErrorResponse",
        ],
        "capabilities": [
            "typed_sdk_exceptions",
            "stable_error_codes",
            "serializable_error_records",
            "non_throwing_error_response",
            "legacy_error_normalization",
            "runtime_error_bridge",
        ],
        "foundation_compatibility": "foundation-v1.0 frozen compatible",
        "cli_compatibility": "stage-06.9 cli freeze compatible",
        "sdk_core_compatibility": "stage-07.0 sdk core compatible",
        "sdk_session_compatibility": "stage-07.1 sdk session api compatible",
        "sdk_translation_compatibility": "stage-07.2 sdk translation api compatible",
        "sdk_batch_compatibility": "stage-07.3 sdk batch api compatible",
        "sdk_streaming_compatibility": "stage-07.4 sdk streaming api compatible",
        "backward_compatible": True,
        "metadata": dict(metadata or {}),
    }
