from __future__ import annotations

from typing import Any, Dict, List, Optional
import time


def create_executor_trace(executor_id: str) -> Dict[str, Any]:
    return {"executor_id": executor_id, "events": [], "created_at": time.time()}


def add_executor_event(trace: Dict[str, Any], event_type: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    trace.setdefault("events", []).append({
        "type": event_type,
        "payload": payload or {},
        "timestamp": time.time(),
    })
    return trace


def validate_executor_trace(trace: Dict[str, Any]) -> bool:
    return isinstance(trace, dict) and isinstance(trace.get("events"), list)
