from __future__ import annotations

import json
from typing import Any, Dict, Optional

from ..command import CLICommand, CommandRegistry
from ..context import CLIContext
from ..result import CLIResult
from .manifest import attach_session_manifest
from .session_store import CLISessionStore, ensure_demo_session


def _store(context: CLIContext, args: object) -> CLISessionStore:
    session_dir = getattr(args, "session_dir", None) or "sessions"
    return CLISessionStore(context.root, session_dir=session_dir)


def _state(args: object) -> Dict[str, Any]:
    value = getattr(args, "state_json", None)
    if not value:
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("--state-json must be a JSON object")
    return parsed


def _result(message: str, payload: Dict[str, Any]) -> CLIResult:
    attach_session_manifest(payload)
    return CLIResult.success(message, **payload)


def command_session(context: CLIContext, args: object) -> CLIResult:
    try:
        action = getattr(args, "session_action", None) or "list"
        store = _store(context, args)

        if action == "create":
            record = store.create(
                session_id=getattr(args, "session_id", None),
                job_id=getattr(args, "job_id", "default-job"),
                metadata={"source": "cli"},
            )
            return _result("Session created", {"session": record.to_dict(), "store": store.manifest()})

        if action == "list":
            records = [record.to_dict() for record in store.list(status=getattr(args, "status", None))]
            return _result("Session list", {"sessions": records, "count": len(records), "store": store.manifest()})

        if action == "info":
            record = store.require(getattr(args, "session_id"))
            checkpoint = store.restore(record.session_id)
            data = {"session": record.to_dict(), "checkpoint": checkpoint.to_dict() if checkpoint else None, "store": store.manifest()}
            return _result("Session info", data)

        if action == "resume":
            record = store.update_status(getattr(args, "session_id"), "running", resumed=True)
            checkpoint = store.restore(record.session_id)
            return _result("Session resumed", {"session": record.to_dict(), "checkpoint": checkpoint.to_dict() if checkpoint else None})

        if action == "pause":
            record = store.update_status(getattr(args, "session_id"), "paused")
            return _result("Session paused", {"session": record.to_dict()})

        if action == "stop":
            record = store.update_status(getattr(args, "session_id"), "stopped")
            return _result("Session stopped", {"session": record.to_dict()})

        if action == "checkpoint":
            checkpoint = store.checkpoint(
                getattr(args, "session_id"),
                segment_index=int(getattr(args, "segment", 0) or 0),
                state=_state(args),
            )
            return _result("Session checkpoint saved", {"checkpoint": checkpoint.to_dict()})

        if action == "restore":
            checkpoint = store.restore(getattr(args, "session_id"))
            if checkpoint is None:
                return CLIResult.failure("Session checkpoint not found", exit_code=2, errors=["checkpoint not found"])
            return _result("Session checkpoint restored", {"checkpoint": checkpoint.to_dict()})

        if action == "cleanup":
            result = store.cleanup(statuses=getattr(args, "status", None), all_sessions=bool(getattr(args, "all", False)))
            result["store"] = store.manifest()
            return _result("Session cleanup", result)

        if action == "demo":
            record = ensure_demo_session(store)
            return _result("Session demo ready", {"session": record.to_dict(), "store": store.manifest()})

        return CLIResult.failure(f"Unknown session action: {action}", exit_code=2)
    except Exception as exc:
        return CLIResult.failure(f"Session command failed: {exc}", exit_code=2)


def register_session_command(registry: CommandRegistry) -> CommandRegistry:
    registry.register(CLICommand("session", "manage NTPE runtime sessions", command_session))
    return registry


__all__ = ["command_session", "register_session_command"]
