"""Public SDK contracts for NTPE 1.0 Beta Stage-07.0.

This module is additive and does not modify frozen Foundation or CLI contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SDKRequest:
    """Stable SDK request object used by application integrations."""

    text: str
    source_language: str = "ko"
    target_language: str = "zh-TW"
    job_id: str = "sdk-job"
    model: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "job_id": self.job_id,
            "model": self.model,
            "metadata": dict(self.metadata),
        }


@dataclass
class SDKResult:
    """Stable SDK result object returned by the public client."""

    ok: bool
    text: str = ""
    job_id: str = "sdk-job"
    session_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "text": self.text,
            "job_id": self.job_id,
            "session_id": self.session_id,
            "data": dict(self.data),
            "errors": list(self.errors),
        }

    @classmethod
    def success(cls, text: str, *, job_id: str = "sdk-job", session_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> "SDKResult":
        return cls(ok=True, text=text, job_id=job_id, session_id=session_id, data=dict(data or {}))

    @classmethod
    def failure(cls, message: str, *, job_id: str = "sdk-job", data: Optional[Dict[str, Any]] = None) -> "SDKResult":
        return cls(ok=False, text="", job_id=job_id, data=dict(data or {}), errors=[str(message)])
