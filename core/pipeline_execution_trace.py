"""
NTPE Foundation-04.5
Pipeline Execution Trace

Additive execution trace layer for the Foundation-04.4 Pipeline State Contract.

Design goals:
- Do not replace Pipeline State Contract.
- Preserve unknown/custom trace fields.
- Provide deterministic event records for stage, plugin, adapter, payload, and error lifecycles.
- Allow Production Pipeline to attach an auditable trace under state['execution_trace'].
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Tuple

try:
    from core.pipeline_state_contract import normalize_pipeline_state, utc_now_iso
except Exception:  # pragma: no cover - compatibility fallback for partial installs
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def normalize_pipeline_state(state: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        return deepcopy(dict(state or {}))


TRACE_VERSION = "04.5"

VALID_EVENT_TYPES = {
    "trace",
    "stage",
    "plugin",
    "adapter",
    "payload",
    "quality",
    "narrative",
    "prompt",
    "context",
    "error",
    "warning",
}

VALID_EVENT_STATUS = {
    "created",
    "started",
    "running",
    "completed",
    "failed",
    "skipped",
    "attached",
    "applied",
    "validated",
    "warning",
}

DEFAULT_TRACE = {
    "trace_version": TRACE_VERSION,
    "trace_id": None,
    "events": [],
    "summary": {
        "event_count": 0,
        "stage_event_count": 0,
        "plugin_event_count": 0,
        "adapter_event_count": 0,
        "error_event_count": 0,
        "warning_event_count": 0,
    },
    "runtime": {
        "created_at": None,
        "updated_at": None,
        "completed_at": None,
    },
}


class NTPEExecutionTraceError(Exception):
    """Raised when execution trace data violates the stable trace contract."""


@dataclass(frozen=True)
class ExecutionTraceResult:
    ok: bool
    trace: Dict[str, Any]
    warnings: Tuple[str, ...] = field(default_factory=tuple)


def _ensure_mapping(value: Any, key: str) -> Dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise NTPEExecutionTraceError(f"{key} must be a mapping")
    return deepcopy(dict(value))


def _ensure_list(value: Any, key: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise NTPEExecutionTraceError(f"{key} must be a list")
    return deepcopy(value)


def _make_trace_id() -> str:
    stamp = utc_now_iso().replace(":", "").replace("-", "")
    return f"ntpe-trace-{stamp}"


def _normalize_event(event: Mapping[str, Any], index: int) -> Dict[str, Any]:
    incoming = _ensure_mapping(event, "event")
    event_type = str(incoming.get("type") or incoming.get("event_type") or "trace")
    status = str(incoming.get("status") or incoming.get("event") or "running")

    if event_type not in VALID_EVENT_TYPES:
        raise NTPEExecutionTraceError(f"invalid trace event type: {event_type}")
    if status not in VALID_EVENT_STATUS:
        raise NTPEExecutionTraceError(f"invalid trace event status: {status}")

    normalized = deepcopy(incoming)
    normalized["index"] = int(normalized.get("index", index))
    normalized["type"] = event_type
    normalized["status"] = status
    normalized["name"] = normalized.get("name") or normalized.get("stage") or normalized.get("plugin") or normalized.get("adapter")
    normalized["message"] = str(normalized.get("message") or "")
    normalized["time"] = str(normalized.get("time") or utc_now_iso())
    normalized.setdefault("metadata", {})
    if not isinstance(normalized["metadata"], Mapping):
        raise NTPEExecutionTraceError("event.metadata must be a mapping")
    normalized["metadata"] = deepcopy(dict(normalized["metadata"]))
    return normalized


def normalize_execution_trace(trace: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Normalize execution trace while preserving forward-compatible custom fields."""
    incoming = deepcopy(dict(trace or {}))
    normalized = deepcopy(DEFAULT_TRACE)

    # Legacy aliases.
    if "events" not in incoming and "trace" in incoming:
        incoming["events"] = incoming.get("trace")
    if "trace_id" not in incoming and "id" in incoming:
        incoming["trace_id"] = incoming.get("id")

    for key, value in incoming.items():
        if key == "events":
            normalized["events"] = _ensure_list(value, "events")
        elif key == "summary":
            summary = deepcopy(DEFAULT_TRACE["summary"])
            summary.update(_ensure_mapping(value, "summary"))
            normalized["summary"] = summary
        elif key == "runtime":
            runtime = deepcopy(DEFAULT_TRACE["runtime"])
            runtime.update(_ensure_mapping(value, "runtime"))
            normalized["runtime"] = runtime
        else:
            normalized[key] = deepcopy(value)

    normalized["trace_version"] = str(normalized.get("trace_version") or TRACE_VERSION)
    normalized["trace_id"] = normalized.get("trace_id") or _make_trace_id()

    normalized["events"] = [
        _normalize_event(event, index)
        for index, event in enumerate(normalized["events"], start=1)
    ]

    normalized["summary"]["event_count"] = len(normalized["events"])
    normalized["summary"]["stage_event_count"] = sum(1 for e in normalized["events"] if e["type"] == "stage")
    normalized["summary"]["plugin_event_count"] = sum(1 for e in normalized["events"] if e["type"] == "plugin")
    normalized["summary"]["adapter_event_count"] = sum(1 for e in normalized["events"] if e["type"] == "adapter")
    normalized["summary"]["error_event_count"] = sum(1 for e in normalized["events"] if e["type"] == "error" or e["status"] == "failed")
    normalized["summary"]["warning_event_count"] = sum(1 for e in normalized["events"] if e["type"] == "warning" or e["status"] == "warning")

    if normalized["runtime"].get("created_at") is None:
        normalized["runtime"]["created_at"] = utc_now_iso()
    if normalized["runtime"].get("updated_at") is None:
        normalized["runtime"]["updated_at"] = normalized["runtime"]["created_at"]

    return normalized


def validate_execution_trace(trace: Mapping[str, Any]) -> ExecutionTraceResult:
    """Validate and normalize execution trace without mutating caller input."""
    warnings: list[str] = []
    normalized = normalize_execution_trace(trace)

    if normalized["summary"]["event_count"] == 0:
        warnings.append("execution trace has no events")

    failed_events = [event for event in normalized["events"] if event["status"] == "failed"]
    if failed_events and normalized["runtime"].get("completed_at"):
        warnings.append("execution trace has failed events but completed_at is set")

    return ExecutionTraceResult(ok=True, trace=normalized, warnings=tuple(warnings))


def create_execution_trace(*, trace_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a new Foundation-04.5 execution trace."""
    now = utc_now_iso()
    return normalize_execution_trace({
        "trace_version": TRACE_VERSION,
        "trace_id": trace_id,
        "events": [{
            "type": "trace",
            "status": "created",
            "name": "execution_trace",
            "message": "execution trace created",
            "time": now,
        }],
        "runtime": {
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
        },
    })


def append_trace_event(
    trace: Mapping[str, Any],
    event_type: str,
    status: str,
    *,
    name: Optional[str] = None,
    message: str = "",
    metadata: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Append a normalized event and recalculate trace summary."""
    updated = normalize_execution_trace(trace)
    updated["events"].append({
        "type": event_type,
        "status": status,
        "name": name,
        "message": message,
        "time": utc_now_iso(),
        "metadata": deepcopy(dict(metadata or {})),
    })
    updated["runtime"]["updated_at"] = utc_now_iso()
    if status == "completed" and event_type == "trace":
        updated["runtime"]["completed_at"] = updated["runtime"]["updated_at"]
    return normalize_execution_trace(updated)


def begin_trace_stage(trace: Mapping[str, Any], stage: str, *, metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    return append_trace_event(trace, "stage", "started", name=stage, metadata=metadata)


def complete_trace_stage(trace: Mapping[str, Any], stage: str, *, metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    return append_trace_event(trace, "stage", "completed", name=stage, metadata=metadata)


def fail_trace_stage(trace: Mapping[str, Any], stage: str, error: Any, *, metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    return append_trace_event(trace, "error", "failed", name=stage, message=str(error), metadata=metadata)


def record_trace_plugin(trace: Mapping[str, Any], plugin_name: str, event: str = "applied") -> Dict[str, Any]:
    return append_trace_event(trace, "plugin", event, name=plugin_name)


def record_trace_adapter(trace: Mapping[str, Any], adapter_name: str, event: str = "applied") -> Dict[str, Any]:
    return append_trace_event(trace, "adapter", event, name=adapter_name)


def attach_trace_to_state(state: Mapping[str, Any], trace: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Attach an execution trace under state['execution_trace'] without breaking existing state fields."""
    updated = normalize_pipeline_state(state)
    updated["execution_trace"] = normalize_execution_trace(trace or updated.get("execution_trace") or create_execution_trace())
    if "runtime" in updated and isinstance(updated["runtime"], Mapping):
        updated["runtime"]["updated_at"] = utc_now_iso()
    return normalize_pipeline_state(updated)


def state_trace_event(
    state: Mapping[str, Any],
    event_type: str,
    status: str,
    *,
    name: Optional[str] = None,
    message: str = "",
    metadata: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Append one execution-trace event directly to a Pipeline State."""
    updated = attach_trace_to_state(state)
    updated["execution_trace"] = append_trace_event(
        updated["execution_trace"],
        event_type,
        status,
        name=name,
        message=message,
        metadata=metadata,
    )
    if "runtime" in updated and isinstance(updated["runtime"], Mapping):
        updated["runtime"]["updated_at"] = utc_now_iso()
    return normalize_pipeline_state(updated)
