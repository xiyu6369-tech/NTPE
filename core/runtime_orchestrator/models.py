"""RM-6.4.0 Runtime Orchestrator domain models.

Immutable dataclasses for execution context and result.
No provider imports. No network calls.
No Translation Engine modifications.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deterministic_hash(*parts: str) -> str:
    joined = "\x00".join(parts)
    return sha256(joined.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RuntimeExecutionContext:
    session_id: str = ""
    snapshot_id: str = ""
    prompt_hash: str = ""
    request_hash: str = ""
    current_chunk: int = 0
    total_chunks: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    version: str = "rm-6.4.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "snapshot_id": self.snapshot_id,
            "prompt_hash": self.prompt_hash,
            "request_hash": self.request_hash,
            "current_chunk": self.current_chunk,
            "total_chunks": self.total_chunks,
            "metadata": dict(self.metadata),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RuntimeExecutionContext":
        return cls(
            session_id=str(payload.get("session_id", "")),
            snapshot_id=str(payload.get("snapshot_id", "")),
            prompt_hash=str(payload.get("prompt_hash", "")),
            request_hash=str(payload.get("request_hash", "")),
            current_chunk=int(payload.get("current_chunk", 0)),
            total_chunks=int(payload.get("total_chunks", 0)),
            metadata=dict(payload.get("metadata") or {}),
        )


@dataclass(frozen=True)
class RuntimeExecutionResult:
    session: Dict[str, Any] = field(default_factory=dict)
    request: Dict[str, Any] = field(default_factory=dict)
    response: Dict[str, Any] = field(default_factory=dict)
    trace: Dict[str, Any] = field(default_factory=dict)
    checkpoint: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    version: str = "rm-6.4.0"

    @property
    def succeeded(self) -> bool:
        return self.response.get("status") == "success"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session": dict(self.session),
            "request": dict(self.request),
            "response": dict(self.response),
            "trace": dict(self.trace),
            "checkpoint": dict(self.checkpoint),
            "metadata": dict(self.metadata),
            "version": self.version,
            "succeeded": self.succeeded,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RuntimeExecutionResult":
        return cls(
            session=dict(payload.get("session") or {}),
            request=dict(payload.get("request") or {}),
            response=dict(payload.get("response") or {}),
            trace=dict(payload.get("trace") or {}),
            checkpoint=dict(payload.get("checkpoint") or {}),
            metadata=dict(payload.get("metadata") or {}),
        )


__all__ = [
    "RuntimeExecutionContext",
    "RuntimeExecutionResult",
    "utc_now_iso",
]