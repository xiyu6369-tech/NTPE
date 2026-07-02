"""Runtime Session API for NTPE 1.0 Beta Stage-11.2."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .runtime_api import RuntimeApi
from .runtime_context import RuntimeApiContext
from .runtime_errors import RuntimeApiNotFoundError, RuntimeApiValidationError
from .runtime_request import RuntimeApiRequest
from .runtime_session import RuntimeSession, RuntimeSessionState


class RuntimeSessionApi:
    """Additive session facade that registers session operations on RuntimeApi."""

    operations = (
        "session.create",
        "session.get",
        "session.list",
        "session.activate",
        "session.pause",
        "session.complete",
        "session.fail",
        "session.cancel",
        "session.resume_state",
    )

    def __init__(self, runtime_api: Optional[RuntimeApi] = None, *, context: Optional[RuntimeApiContext] = None) -> None:
        self.runtime_api = runtime_api or RuntimeApi(context=context)
        self._sessions: Dict[str, RuntimeSession] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.runtime_api.register("session.create", self._handle_create)
        self.runtime_api.register("session.get", self._handle_get)
        self.runtime_api.register("session.list", self._handle_list)
        self.runtime_api.register("session.activate", self._handle_activate)
        self.runtime_api.register("session.pause", self._handle_pause)
        self.runtime_api.register("session.complete", self._handle_complete)
        self.runtime_api.register("session.fail", self._handle_fail)
        self.runtime_api.register("session.cancel", self._handle_cancel)
        self.runtime_api.register("session.resume_state", self._handle_resume_state)

    def create(self, *, name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> RuntimeSession:
        session = RuntimeSession(name=name, metadata=dict(metadata or {}))
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> RuntimeSession:
        session = self._sessions.get(str(session_id))
        if session is None:
            raise RuntimeApiNotFoundError("runtime session not found", details={"session_id": str(session_id)})
        return session

    def list(self) -> tuple[RuntimeSession, ...]:
        return tuple(self._sessions.values())

    def transition(self, session_id: str, state: RuntimeSessionState | str, *, metadata: Optional[Dict[str, Any]] = None) -> RuntimeSession:
        session = self.get(session_id)
        updated = session.transition(state, metadata=metadata)
        self._sessions[updated.session_id] = updated
        return updated

    def resume_state(self, session_id: str) -> Dict[str, Any]:
        session = self.get(session_id)
        return {
            "session_id": session.session_id,
            "state": session.state.value,
            "resumable": session.state in {RuntimeSessionState.CREATED, RuntimeSessionState.ACTIVE, RuntimeSessionState.PAUSED},
            "metadata": dict(session.metadata),
            "updated_at": session.updated_at,
        }

    def _session_id_from(self, request: RuntimeApiRequest) -> str:
        session_id = request.payload.get("session_id")
        if not session_id:
            raise RuntimeApiValidationError("session_id is required", details={"operation": request.operation})
        return str(session_id)

    def _handle_create(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        session = self.create(name=request.payload.get("name"), metadata=request.payload.get("metadata") or {})
        return session.to_dict()

    def _handle_get(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.get(self._session_id_from(request)).to_dict()

    def _handle_list(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return {"sessions": [session.to_dict() for session in self.list()], "count": len(self._sessions)}

    def _handle_activate(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._session_id_from(request), RuntimeSessionState.ACTIVE, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_pause(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._session_id_from(request), RuntimeSessionState.PAUSED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_complete(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._session_id_from(request), RuntimeSessionState.COMPLETED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_fail(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._session_id_from(request), RuntimeSessionState.FAILED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_cancel(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.transition(self._session_id_from(request), RuntimeSessionState.CANCELLED, metadata=request.payload.get("metadata") or {}).to_dict()

    def _handle_resume_state(self, request: RuntimeApiRequest, context: RuntimeApiContext) -> Dict[str, Any]:
        return self.resume_state(self._session_id_from(request))


def attach_session_api(runtime_api: Optional[RuntimeApi] = None, *, context: Optional[RuntimeApiContext] = None) -> RuntimeSessionApi:
    return RuntimeSessionApi(runtime_api=runtime_api, context=context)
