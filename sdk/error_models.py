"""Stage-07.5 SDK Error Handling API model objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .error_codes import SDKErrorCode, SDK_ERROR_STAGE, SDK_ERROR_VERSION


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SDKErrorContext:
    """Context attached to SDK errors without changing legacy APIs."""

    stage: str = SDK_ERROR_STAGE
    version: str = SDK_ERROR_VERSION
    job_id: str = "sdk-job"
    session_id: Optional[str] = None
    component: str = "sdk"
    operation: str = "unknown"
    retryable: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "version": self.version,
            "job_id": self.job_id,
            "session_id": self.session_id,
            "component": self.component,
            "operation": self.operation,
            "retryable": self.retryable,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | None) -> "SDKErrorContext":
        payload = dict(data or {})
        return cls(
            stage=str(payload.get("stage", SDK_ERROR_STAGE)),
            version=str(payload.get("version", SDK_ERROR_VERSION)),
            job_id=str(payload.get("job_id", "sdk-job")),
            session_id=payload.get("session_id"),
            component=str(payload.get("component", "sdk")),
            operation=str(payload.get("operation", "unknown")),
            retryable=bool(payload.get("retryable", False)),
            metadata=dict(payload.get("metadata", {}) or {}),
        )


@dataclass
class SDKErrorRecord:
    """Serializable SDK error record used by all Stage-07.5 helpers."""

    code: SDKErrorCode = SDKErrorCode.UNKNOWN
    message: str = "Unknown SDK error"
    context: SDKErrorContext = field(default_factory=SDKErrorContext)
    cause: Optional[str] = None
    timestamp: str = field(default_factory=_utc_now)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code.value,
            "message": self.message,
            "context": self.context.to_dict(),
            "cause": self.cause,
            "timestamp": self.timestamp,
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SDKErrorRecord":
        payload = dict(data or {})
        return cls(
            code=SDKErrorCode.coerce(payload.get("code")),
            message=str(payload.get("message", "Unknown SDK error")),
            context=SDKErrorContext.from_dict(payload.get("context")),
            cause=payload.get("cause"),
            timestamp=str(payload.get("timestamp") or _utc_now()),
            details=dict(payload.get("details", {}) or {}),
        )
