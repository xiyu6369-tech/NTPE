"""Stage-07.5 SDK Error Handling API response object."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .error_codes import SDKErrorCode
from .error_models import SDKErrorContext, SDKErrorRecord


@dataclass
class SDKErrorResponse:
    """Standardized non-throwing SDK error response."""

    ok: bool = False
    code: SDKErrorCode = SDKErrorCode.UNKNOWN
    message: str = "Unknown SDK error"
    job_id: str = "sdk-job"
    session_id: Optional[str] = None
    errors: List[SDKErrorRecord] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.code = SDKErrorCode.coerce(self.code)
        if not self.errors:
            self.errors.append(
                SDKErrorRecord(
                    code=self.code,
                    message=self.message,
                    context=SDKErrorContext(job_id=self.job_id, session_id=self.session_id),
                )
            )

    @property
    def error_messages(self) -> List[str]:
        return [error.message for error in self.errors]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "code": self.code.value,
            "message": self.message,
            "job_id": self.job_id,
            "session_id": self.session_id,
            "errors": [error.to_dict() for error in self.errors],
            "data": dict(self.data),
        }

    @classmethod
    def from_error(cls, error: SDKErrorRecord, *, data: Optional[Dict[str, Any]] = None) -> "SDKErrorResponse":
        return cls(
            ok=False,
            code=error.code,
            message=error.message,
            job_id=error.context.job_id,
            session_id=error.context.session_id,
            errors=[error],
            data=dict(data or {}),
        )
