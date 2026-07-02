"""Stage-07.1 SDK Session API.

This module is additive and uses the Stage-07.0 NTPEClient facade without
changing frozen Foundation or CLI contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional
import time
import uuid

from .client import NTPEClient
from .contracts import SDKResult
from .exceptions import SDKSessionError

SDK_SESSION_VERSION = "0.7.1"
SDK_SESSION_STAGE = "NTPE 1.0 Beta Stage-07.1 SDK Session API"
SDKCallback = Callable[[Dict[str, Any]], None]


@dataclass
class SDKSessionStatus:
    session_id: str
    job_id: str
    status: str = "created"
    current_index: int = 0
    total_segments: int = 0
    result_count: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def progress_percent(self) -> float:
        if self.total_segments <= 0:
            return 100.0 if self.status == "completed" else 0.0
        return round((self.current_index / self.total_segments) * 100.0, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "job_id": self.job_id,
            "status": self.status,
            "current_index": self.current_index,
            "total_segments": self.total_segments,
            "result_count": self.result_count,
            "progress_percent": self.progress_percent,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }


class SDKSession:
    """Public long-running translation session wrapper for Python callers."""

    version = SDK_SESSION_VERSION
    stage = SDK_SESSION_STAGE

    def __init__(
        self,
        *,
        client: Optional[NTPEClient] = None,
        job_id: str = "sdk-session-job",
        session_id: Optional[str] = None,
        segments: Optional[Iterable[str]] = None,
        source_language: str = "ko",
        target_language: str = "zh-TW",
        model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        on_event: Optional[SDKCallback] = None,
    ):
        self.client = client or NTPEClient()
        self.segments = list(segments or [])
        self.source_language = source_language
        self.target_language = target_language
        self.model = model
        self.callbacks: List[SDKCallback] = []
        if on_event is not None:
            self.callbacks.append(on_event)
        self.results: List[SDKResult] = []
        self.events: List[Dict[str, Any]] = []
        self.status = SDKSessionStatus(
            session_id=session_id or f"sdk-{uuid.uuid4().hex[:12]}",
            job_id=job_id,
            total_segments=len(self.segments),
            metadata=dict(metadata or {}),
        )
        self._emit("created")

    @classmethod
    def create(cls, **kwargs: Any) -> "SDKSession":
        return cls(**kwargs)

    def add_callback(self, callback: SDKCallback) -> "SDKSession":
        self.callbacks.append(callback)
        return self

    def start(self, segments: Optional[Iterable[str]] = None) -> "SDKSession":
        if segments is not None:
            self.segments = list(segments)
            self.status.total_segments = len(self.segments)
        if self.status.status == "completed":
            return self
        self.status.status = "running"
        self._touch()
        self._emit("started")
        self._run_from(self.status.current_index)
        return self

    def resume(self, segments: Optional[Iterable[str]] = None) -> "SDKSession":
        if segments is not None:
            self.segments = list(segments)
            self.status.total_segments = len(self.segments)
        if self.status.status == "completed":
            self._emit("resume_skipped")
            return self
        self.status.status = "running"
        self._touch()
        self._emit("resumed")
        self._run_from(self.status.current_index)
        return self

    def progress(self) -> Dict[str, Any]:
        return self.status.to_dict()

    def get_status(self) -> SDKSessionStatus:
        return self.status

    def result(self) -> Dict[str, Any]:
        return {
            "type": "sdk_session_result",
            "version": self.version,
            "stage": self.stage,
            "session": self.status.to_dict(),
            "results": [item.to_dict() for item in self.results],
            "events": list(self.events),
            "ok": self.status.status == "completed" and all(item.ok for item in self.results),
        }

    def checkpoint(self) -> Dict[str, Any]:
        return self.result()

    @classmethod
    def from_checkpoint(cls, checkpoint: Dict[str, Any], *, client: Optional[NTPEClient] = None, segments: Optional[Iterable[str]] = None) -> "SDKSession":
        session_data = dict(checkpoint.get("session", {}))
        session = cls(
            client=client,
            job_id=str(session_data.get("job_id", "sdk-session-job")),
            session_id=str(session_data.get("session_id") or f"sdk-{uuid.uuid4().hex[:12]}"),
            segments=segments or [],
            metadata=dict(session_data.get("metadata", {}) or {}),
        )
        session.status.status = str(session_data.get("status", "created"))
        session.status.current_index = int(session_data.get("current_index", 0))
        session.status.total_segments = int(session_data.get("total_segments", len(session.segments)))
        session.status.result_count = int(session_data.get("result_count", 0))
        session.status.created_at = float(session_data.get("created_at", session.status.created_at))
        session.status.updated_at = float(session_data.get("updated_at", session.status.updated_at))
        restored_results = []
        for item in checkpoint.get("results", []):
            restored_results.append(SDKResult(
                ok=bool(item.get("ok")),
                text=str(item.get("text", "")),
                job_id=str(item.get("job_id", session.status.job_id)),
                session_id=item.get("session_id"),
                data=dict(item.get("data", {}) or {}),
                errors=list(item.get("errors", []) or []),
            ))
        session.results = restored_results
        session.events = list(checkpoint.get("events", []) or [])
        return session

    def manifest(self) -> Dict[str, Any]:
        return build_sdk_session_manifest({"client_version": getattr(self.client, "version", None)})

    def _run_from(self, start_index: int) -> None:
        if not self.segments:
            self.status.status = "completed"
            self._touch()
            self._emit("completed")
            return
        for index in range(start_index, len(self.segments)):
            segment = self.segments[index]
            self._emit("segment_started", {"index": index})
            result = self.client.translate_text(
                segment,
                source_language=self.source_language,
                target_language=self.target_language,
                job_id=self.status.job_id,
                model=self.model,
                metadata={"sdk_session_id": self.status.session_id, "segment_index": index},
            )
            self.results.append(result)
            self.status.current_index = index + 1
            self.status.result_count = len(self.results)
            self._touch()
            self._emit("segment_completed", {"index": index, "ok": result.ok})
            if not result.ok:
                self.status.status = "failed"
                self._touch()
                self._emit("failed", {"index": index, "errors": list(result.errors)})
                raise SDKSessionError("SDK session translation failed")
        self.status.status = "completed"
        self._touch()
        self._emit("completed")

    def _touch(self) -> None:
        self.status.updated_at = time.time()

    def _emit(self, name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        event = {
            "type": "sdk_session_event",
            "name": name,
            "session_id": self.status.session_id,
            "job_id": self.status.job_id,
            "status": self.status.status,
            "current_index": self.status.current_index,
            "total_segments": self.status.total_segments,
            "progress_percent": self.status.progress_percent,
            "payload": dict(payload or {}),
            "created_at": time.time(),
        }
        self.events.append(event)
        for callback in list(self.callbacks):
            callback(dict(event))


def create_session(**kwargs: Any) -> SDKSession:
    return SDKSession.create(**kwargs)


def build_sdk_session_manifest(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": "NTPE SDK Session API",
        "stage": SDK_SESSION_STAGE,
        "version": SDK_SESSION_VERSION,
        "status": "beta",
        "components": [
            "SDKSession",
            "SDKSessionStatus",
            "create_session",
            "SDK callback events",
            "checkpoint_resume",
        ],
        "capabilities": [
            "create_session",
            "start_session",
            "resume_session",
            "session_status",
            "session_progress",
            "session_result",
            "event_callback",
            "client_runtime_reuse",
        ],
        "foundation_compatibility": "foundation-v1.0 frozen compatible",
        "cli_compatibility": "stage-06.9 cli freeze compatible",
        "sdk_core_compatibility": "stage-07.0 sdk core compatible",
        "backward_compatible": True,
        "metadata": dict(metadata or {}),
    }
