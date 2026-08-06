"""RM-6.3.1 Runtime Session Manager.

Coordinates the lifecycle of a translation session through
TranslationSession, RuntimeState, and SessionTrace — all
in-memory. No network calls. No provider imports. No file
persistence. No Translation Engine modifications.

Architecture:
    TranslationRequest
            │
            ▼
    RuntimeSessionManager
            │
            ▼
    TranslationSession
            │
            ├── RuntimeState
            ├── SessionTrace
            └── Metadata
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.runtime_session.models import (
    TranslationSession,
    RuntimeState,
    RunStatus,
    SessionTrace,
    TraceEntry,
    utc_now_iso,
)


class RuntimeSessionManager:
    """Create, load, update, trace, and finish translation sessions."""

    version = "rm-6.3.1"

    def __init__(self):
        self._sessions: Dict[str, TranslationSession] = {}
        self._states: Dict[str, RuntimeState] = {}
        self._traces: Dict[str, SessionTrace] = {}

    def create_session(
        self,
        snapshot_id: str = "",
        prompt_hash: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TranslationSession:
        session = TranslationSession(
            snapshot_id=snapshot_id,
            prompt_hash=prompt_hash,
            metadata=dict(metadata or {}),
        )
        self._sessions[session.session_id] = session
        self._states[session.session_id] = RuntimeState(
            session_id=session.session_id,
        )
        self._traces[session.session_id] = SessionTrace(
            session_id=session.session_id,
        )
        return session

    def load_session(self, session_id: str) -> Optional[TranslationSession]:
        return self._sessions.get(session_id)

    def save_session(self, session: TranslationSession) -> None:
        self._sessions[session.session_id] = session

    def update_runtime(
        self,
        session_id: str,
        *,
        current_chunk: Optional[int] = None,
        total_chunks: Optional[int] = None,
        status: Optional[RunStatus] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RuntimeState:
        state = self._states.get(session_id)
        if state is None:
            raise KeyError(f"No runtime state for session: {session_id}")

        if status is not None:
            state = state.transition(status)

        kwargs: Dict[str, Any] = {}
        if current_chunk is not None:
            kwargs["current_chunk"] = current_chunk
        if total_chunks is not None:
            kwargs["total_chunks"] = total_chunks
        if metadata is not None:
            kwargs["metadata"] = {**state.metadata, **metadata}
        if "status" not in kwargs:
            kwargs["status"] = state.status

        kwargs["session_id"] = state.session_id
        kwargs["current_chunk"] = kwargs.get("current_chunk", state.current_chunk)
        kwargs["total_chunks"] = kwargs.get("total_chunks", state.total_chunks)
        kwargs["last_request"] = state.last_request
        kwargs["last_response"] = state.last_response

        updated = RuntimeState(**{
            k: v for k, v in kwargs.items()
            if k in {f.name for f in type(state).__dataclass_fields__.values()}
        })

        self._states[session_id] = updated
        return updated

    def append_trace(
        self,
        session_id: str,
        request_hash: str,
        snapshot_id: str,
        chunk: int,
    ) -> SessionTrace:
        trace = self._traces.get(session_id)
        if trace is None:
            raise ValueError(f"No trace for session: {session_id}")

        entry = TraceEntry(
            request_hash=request_hash,
            snapshot_id=snapshot_id,
            chunk=chunk,
        )
        updated = trace.append(entry)
        self._traces[session_id] = updated
        return updated

    def finish_session(
        self,
        session_id: str,
        success: bool = True,
    ) -> TranslationSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"No session found: {session_id}")

        state = self._states.get(session_id)
        if state is None:
            raise ValueError(f"No runtime state for session: {session_id}")

        target = RunStatus.COMPLETED if success else RunStatus.FAILED
        self.update_runtime(session_id, status=target)

        return session

    def get_state(self, session_id: str) -> Optional[RuntimeState]:
        return self._states.get(session_id)

    def get_trace(self, session_id: str) -> Optional[SessionTrace]:
        return self._traces.get(session_id)

    def state_for_session(self, session_id: str) -> RuntimeState:
        """Retrieve the runtime state for a session or raise an error.

        This is the canonical way to read state for an existing session.
        """
        state = self._states.get(session_id)
        if state is None:
            raise ValueError(f"No runtime state for session: {session_id}")
        return state

    def trace_for_session(self, session_id: str) -> SessionTrace:
        """Retrieve the trace for a session or raise an error.

        This is the canonical way to read the trace for an existing session.
        """
        trace = self._traces.get(session_id)
        if trace is None:
            raise ValueError(f"No trace for session: {session_id}")
        return trace

    @property
    def active_sessions(self) -> int:
        return len(self._sessions)

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "runtime_session_manager",
            "version": self.version,
            "active_sessions": len(self._sessions),
            "stored_states": len(self._states),
            "stored_traces": len(self._traces),
            "enabled": True,
        }


__all__ = [
    "RuntimeSessionManager",
]