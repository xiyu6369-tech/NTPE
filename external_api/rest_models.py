"""REST API model primitives for NTPE 1.0 Beta Stage-12.1.

This layer is additive. It converts external HTTP-like requests into calls to the
frozen Runtime API facade without importing or mutating lower runtime internals.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

EXTERNAL_API_VERSION = "1.0.0-beta.12.1"
EXTERNAL_API_STAGE = "12.1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class RestRequest:
    """Small HTTP-like request envelope for tests, SDK, and future servers."""

    method: str
    path: str
    body: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    query: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None
    created_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        object.__setattr__(self, "method", str(self.method or "GET").upper())
        path = str(self.path or "/")
        if not path.startswith("/"):
            path = "/" + path
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "body", dict(self.body or {}))
        object.__setattr__(self, "headers", dict(self.headers or {}))
        object.__setattr__(self, "query", dict(self.query or {}))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": EXTERNAL_API_VERSION,
            "stage": EXTERNAL_API_STAGE,
            "method": self.method,
            "path": self.path,
            "body": dict(self.body),
            "headers": dict(self.headers),
            "query": dict(self.query),
            "request_id": self.request_id,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class RestResponse:
    """Serializable REST response envelope."""

    status_code: int
    body: Any = None
    headers: Dict[str, str] = field(default_factory=dict)
    request_id: Optional[str] = None
    created_at: str = field(default_factory=utc_now_iso)

    version = EXTERNAL_API_VERSION
    stage = EXTERNAL_API_STAGE

    def __post_init__(self) -> None:
        object.__setattr__(self, "status_code", int(self.status_code))
        base_headers = {"content-type": "application/json", "x-ntpe-stage": EXTERNAL_API_STAGE}
        base_headers.update(dict(self.headers or {}))
        object.__setattr__(self, "headers", base_headers)

    @classmethod
    def ok(cls, body: Any = None, *, request_id: Optional[str] = None) -> "RestResponse":
        return cls(status_code=200, body=body, request_id=request_id)

    @classmethod
    def created(cls, body: Any = None, *, request_id: Optional[str] = None) -> "RestResponse":
        return cls(status_code=201, body=body, request_id=request_id)

    @classmethod
    def error(cls, status_code: int, message: str, *, request_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> "RestResponse":
        return cls(
            status_code=status_code,
            body={"ok": False, "error": {"message": str(message), "details": dict(details or {})}},
            request_id=request_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "stage": self.stage,
            "status_code": self.status_code,
            "body": self.body,
            "headers": dict(self.headers),
            "request_id": self.request_id,
            "created_at": self.created_at,
        }
