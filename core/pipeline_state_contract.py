"""
NTPE Foundation-04.4
Pipeline State Contract

Additive, backward-compatible state contract for Production Pipeline,
Adapter System, Plugin System, and future Foundation stages.

Design goals:
- Do not replace the payload/context contract from Foundation-04.3.
- Preserve unknown keys for forward compatibility.
- Normalize legacy/minimal state dictionaries into one stable shape.
- Provide deterministic helpers for stage/plugin/adapter lifecycle updates.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Tuple

try:
    from core.context_contract import normalize_context_payload, validate_context_payload
except Exception:  # pragma: no cover - compatibility fallback for partial installs
    def normalize_context_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
        data = deepcopy(dict(payload or {}))
        data.setdefault("source_text", data.get("text", ""))
        data.setdefault("target_language", data.get("language", "繁體中文"))
        data.setdefault("context", {})
        data.setdefault("metadata", {})
        return data

    def validate_context_payload(payload: Mapping[str, Any]):
        class _Result:
            pass
        result = _Result()
        result.ok = True
        result.payload = normalize_context_payload(payload)
        result.warnings = tuple()
        return result


class NTPEPipelineStateError(Exception):
    """Raised when a pipeline state violates the stable NTPE state contract."""


@dataclass(frozen=True)
class PipelineStateResult:
    ok: bool
    state: Dict[str, Any]
    warnings: Tuple[str, ...] = field(default_factory=tuple)


STATE_VERSION = "04.4"

DEFAULT_STATUS = "initialized"
VALID_STATUSES = {
    "initialized",
    "running",
    "completed",
    "failed",
    "skipped",
    "paused",
}

DEFAULT_STATE = {
    "state_version": STATE_VERSION,
    "status": DEFAULT_STATUS,
    "current_stage": None,
    "completed_stages": [],
    "failed_stages": [],
    "adapter_trace": [],
    "plugin_trace": [],
    "errors": [],
    "warnings": [],
    "counters": {
        "stage_count": 0,
        "adapter_count": 0,
        "plugin_count": 0,
        "error_count": 0,
        "warning_count": 0,
    },
    "runtime": {
        "started_at": None,
        "updated_at": None,
        "completed_at": None,
    },
}


_TRACE_KEYS = {
    "completed_stages",
    "failed_stages",
    "adapter_trace",
    "plugin_trace",
    "errors",
    "warnings",
}


def utc_now_iso() -> str:
    """Return a stable UTC ISO timestamp for state runtime fields."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ensure_mapping(value: Any, key: str) -> Dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise NTPEPipelineStateError(f"{key} must be a mapping")
    return deepcopy(dict(value))


def _ensure_list(value: Any, key: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise NTPEPipelineStateError(f"{key} must be a list")
    return deepcopy(value)


def normalize_pipeline_state(state: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """
    Normalize a pipeline state dictionary into the Foundation-04.4 contract.

    Backward compatibility:
    - None or empty state becomes a valid initialized state.
    - Unknown keys are preserved.
    - Legacy aliases are migrated:
        stage -> current_stage
        done_stages -> completed_stages
        failures -> errors
    """
    incoming = deepcopy(dict(state or {}))
    normalized = deepcopy(DEFAULT_STATE)

    # Legacy aliases before merge.
    if "current_stage" not in incoming and "stage" in incoming:
        incoming["current_stage"] = incoming.get("stage")
    if "completed_stages" not in incoming and "done_stages" in incoming:
        incoming["completed_stages"] = incoming.get("done_stages")
    if "errors" not in incoming and "failures" in incoming:
        incoming["errors"] = incoming.get("failures")

    for key, value in incoming.items():
        if key in _TRACE_KEYS:
            normalized[key] = _ensure_list(value, key)
        elif key == "counters":
            counters = deepcopy(DEFAULT_STATE["counters"])
            counters.update(_ensure_mapping(value, "counters"))
            normalized["counters"] = counters
        elif key == "runtime":
            runtime = deepcopy(DEFAULT_STATE["runtime"])
            runtime.update(_ensure_mapping(value, "runtime"))
            normalized["runtime"] = runtime
        else:
            normalized[key] = deepcopy(value)

    normalized["state_version"] = str(normalized.get("state_version") or STATE_VERSION)
    normalized["status"] = str(normalized.get("status") or DEFAULT_STATUS)

    if normalized["status"] not in VALID_STATUSES:
        raise NTPEPipelineStateError(f"invalid status: {normalized['status']}")

    # Recalculate counters from canonical traces, while preserving unrelated custom counters.
    normalized["counters"]["stage_count"] = len(normalized["completed_stages"])
    normalized["counters"]["adapter_count"] = len(normalized["adapter_trace"])
    normalized["counters"]["plugin_count"] = len(normalized["plugin_trace"])
    normalized["counters"]["error_count"] = len(normalized["errors"])
    normalized["counters"]["warning_count"] = len(normalized["warnings"])

    return normalized


def validate_pipeline_state(state: Mapping[str, Any]) -> PipelineStateResult:
    """Validate and normalize a pipeline state without mutating the input."""
    warnings: list[str] = []
    normalized = normalize_pipeline_state(state)

    if normalized["status"] == "failed" and not normalized["errors"]:
        warnings.append("status is failed but errors is empty")

    if normalized["status"] == "completed" and normalized["current_stage"] is not None:
        warnings.append("status is completed but current_stage is not None")

    return PipelineStateResult(ok=True, state=normalized, warnings=tuple(warnings))


def create_pipeline_state(payload: Optional[Mapping[str, Any]] = None, *, stage: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a valid pipeline state. If payload is supplied, it is normalized using
    the Foundation-04.3 context contract and stored under state['payload'].
    """
    now = utc_now_iso()
    state = normalize_pipeline_state({
        "status": "initialized",
        "current_stage": stage,
        "runtime": {
            "started_at": now,
            "updated_at": now,
            "completed_at": None,
        },
    })

    if payload is not None:
        state["payload"] = validate_context_payload(payload).payload

    return state


def update_stage_state(state: Mapping[str, Any], stage: str, status: str = "running") -> Dict[str, Any]:
    """Set current stage and lifecycle status."""
    updated = normalize_pipeline_state(state)
    if status not in VALID_STATUSES:
        raise NTPEPipelineStateError(f"invalid status: {status}")
    updated["current_stage"] = stage
    updated["status"] = status
    updated["runtime"]["updated_at"] = utc_now_iso()
    return normalize_pipeline_state(updated)


def complete_stage_state(state: Mapping[str, Any], stage: Optional[str] = None) -> Dict[str, Any]:
    """Mark a stage as completed while preserving idempotency."""
    updated = normalize_pipeline_state(state)
    stage_name = stage or updated.get("current_stage")
    if stage_name and stage_name not in updated["completed_stages"]:
        updated["completed_stages"].append(stage_name)
    updated["current_stage"] = None
    updated["status"] = "completed"
    updated["runtime"]["updated_at"] = utc_now_iso()
    updated["runtime"]["completed_at"] = updated["runtime"]["updated_at"]
    return normalize_pipeline_state(updated)


def fail_stage_state(state: Mapping[str, Any], stage: Optional[str], error: Any) -> Dict[str, Any]:
    """Mark a stage as failed and append a stable error record."""
    updated = normalize_pipeline_state(state)
    stage_name = stage or updated.get("current_stage")
    if stage_name and stage_name not in updated["failed_stages"]:
        updated["failed_stages"].append(stage_name)
    updated["status"] = "failed"
    updated["current_stage"] = stage_name
    updated["errors"].append({
        "stage": stage_name,
        "message": str(error),
        "time": utc_now_iso(),
    })
    updated["runtime"]["updated_at"] = utc_now_iso()
    return normalize_pipeline_state(updated)


def record_adapter_trace(state: Mapping[str, Any], adapter_name: str, event: str = "applied") -> Dict[str, Any]:
    """Append an adapter trace entry."""
    updated = normalize_pipeline_state(state)
    updated["adapter_trace"].append({
        "adapter": adapter_name,
        "event": event,
        "time": utc_now_iso(),
    })
    updated["runtime"]["updated_at"] = utc_now_iso()
    return normalize_pipeline_state(updated)


def record_plugin_trace(state: Mapping[str, Any], plugin_name: str, event: str = "applied") -> Dict[str, Any]:
    """Append a plugin trace entry."""
    updated = normalize_pipeline_state(state)
    updated["plugin_trace"].append({
        "plugin": plugin_name,
        "event": event,
        "time": utc_now_iso(),
    })
    updated["runtime"]["updated_at"] = utc_now_iso()
    return normalize_pipeline_state(updated)


def attach_payload_to_state(state: Mapping[str, Any], payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Attach a normalized Foundation-04.3 payload to a Foundation-04.4 state."""
    updated = normalize_pipeline_state(state)
    updated["payload"] = validate_context_payload(payload).payload
    updated["runtime"]["updated_at"] = utc_now_iso()
    return normalize_pipeline_state(updated)
