"""
NTPE Foundation-04.6
Pipeline Runtime Guard

Additive runtime validation layer for Foundation-04.3 Context Contract,
Foundation-04.4 Pipeline State Contract, and Foundation-04.5 Execution Trace.

Design goals:
- Do not replace payload/state/trace contracts.
- Validate runtime objects before and after adapters/plugins/stages.
- Repair by normalization when strict=False.
- Fail fast with stable error records when strict=True.
- Preserve unknown/custom fields for forward compatibility.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

try:
    from core.context_contract import normalize_context_payload, validate_context_payload
except Exception:  # pragma: no cover - compatibility fallback
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

try:
    from core.pipeline_state_contract import normalize_pipeline_state, validate_pipeline_state, utc_now_iso
except Exception:  # pragma: no cover - compatibility fallback
    from datetime import datetime, timezone

    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def normalize_pipeline_state(state: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        data = deepcopy(dict(state or {}))
        data.setdefault("state_version", "04.4")
        data.setdefault("status", "initialized")
        data.setdefault("current_stage", None)
        data.setdefault("completed_stages", [])
        data.setdefault("failed_stages", [])
        data.setdefault("adapter_trace", [])
        data.setdefault("plugin_trace", [])
        data.setdefault("errors", [])
        data.setdefault("warnings", [])
        data.setdefault("counters", {})
        data.setdefault("runtime", {})
        return data

    def validate_pipeline_state(state: Mapping[str, Any]):
        class _Result:
            pass
        result = _Result()
        result.ok = True
        result.state = normalize_pipeline_state(state)
        result.warnings = tuple()
        return result

try:
    from core.pipeline_execution_trace import (
        append_trace_event,
        attach_trace_to_state,
        create_execution_trace,
        normalize_execution_trace,
        validate_execution_trace,
    )
except Exception:  # pragma: no cover - compatibility fallback
    def create_execution_trace(*, trace_id: Optional[str] = None) -> Dict[str, Any]:
        return {
            "trace_version": "04.5",
            "trace_id": trace_id or "ntpe-trace-fallback",
            "events": [],
            "summary": {"event_count": 0, "error_event_count": 0, "warning_event_count": 0},
            "runtime": {"created_at": utc_now_iso(), "updated_at": utc_now_iso(), "completed_at": None},
        }

    def normalize_execution_trace(trace: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        data = deepcopy(dict(trace or create_execution_trace()))
        data.setdefault("events", [])
        data.setdefault("summary", {})
        data["summary"]["event_count"] = len(data["events"])
        data.setdefault("runtime", {"created_at": utc_now_iso(), "updated_at": utc_now_iso(), "completed_at": None})
        return data

    def validate_execution_trace(trace: Mapping[str, Any]):
        class _Result:
            pass
        result = _Result()
        result.ok = True
        result.trace = normalize_execution_trace(trace)
        result.warnings = tuple()
        return result

    def append_trace_event(trace: Mapping[str, Any], event_type: str, status: str, *, name: Optional[str] = None, message: str = "", metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        data = normalize_execution_trace(trace)
        data["events"].append({"type": event_type, "status": status, "name": name, "message": message, "time": utc_now_iso(), "metadata": dict(metadata or {})})
        return normalize_execution_trace(data)

    def attach_trace_to_state(state: Mapping[str, Any], trace: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        data = normalize_pipeline_state(state)
        data["execution_trace"] = normalize_execution_trace(trace or data.get("execution_trace") or create_execution_trace())
        return data


GUARD_VERSION = "04.6"
VALID_GUARD_TARGETS = {"payload", "state", "trace", "runtime"}
VALID_GUARD_PHASES = {"before", "after", "validate", "repair", "failed"}


class NTPERuntimeGuardError(Exception):
    """Raised when runtime guard validation fails in strict mode."""


@dataclass(frozen=True)
class RuntimeGuardResult:
    ok: bool
    target: str
    phase: str
    data: Dict[str, Any]
    warnings: Tuple[str, ...] = field(default_factory=tuple)
    errors: Tuple[str, ...] = field(default_factory=tuple)


def _as_mapping(value: Any, key: str) -> Dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise NTPERuntimeGuardError(f"{key} must be a mapping")
    return deepcopy(dict(value))


def _collect_warnings(result: Any) -> Tuple[str, ...]:
    warnings = getattr(result, "warnings", tuple())
    if warnings is None:
        return tuple()
    return tuple(str(item) for item in warnings)


def _guard_event(trace: Mapping[str, Any], phase: str, target: str, *, ok: bool, message: str = "", metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    status = "validated" if ok else "failed"
    return append_trace_event(
        trace,
        "warning" if not ok else "trace",
        status,
        name=f"runtime_guard:{phase}:{target}",
        message=message,
        metadata={"guard_version": GUARD_VERSION, "phase": phase, "target": target, **dict(metadata or {})},
    )


def guard_payload(payload: Mapping[str, Any], *, phase: str = "validate", strict: bool = False) -> RuntimeGuardResult:
    """Validate a Foundation-04.3 payload at runtime."""
    if phase not in VALID_GUARD_PHASES:
        raise NTPERuntimeGuardError(f"invalid guard phase: {phase}")
    try:
        validation = validate_context_payload(_as_mapping(payload, "payload"))
        normalized = deepcopy(validation.payload)
        return RuntimeGuardResult(True, "payload", phase, normalized, _collect_warnings(validation), tuple())
    except Exception as exc:
        if strict:
            raise NTPERuntimeGuardError(f"payload guard failed: {exc}") from exc
        repaired = normalize_context_payload(_as_mapping(payload, "payload"))
        return RuntimeGuardResult(False, "payload", phase, repaired, tuple(), (str(exc),))


def guard_trace(trace: Optional[Mapping[str, Any]] = None, *, phase: str = "validate", strict: bool = False) -> RuntimeGuardResult:
    """Validate a Foundation-04.5 execution trace at runtime."""
    if phase not in VALID_GUARD_PHASES:
        raise NTPERuntimeGuardError(f"invalid guard phase: {phase}")
    try:
        validation = validate_execution_trace(trace or create_execution_trace())
        normalized = deepcopy(validation.trace)
        return RuntimeGuardResult(True, "trace", phase, normalized, _collect_warnings(validation), tuple())
    except Exception as exc:
        if strict:
            raise NTPERuntimeGuardError(f"trace guard failed: {exc}") from exc
        repaired = normalize_execution_trace(trace or create_execution_trace())
        return RuntimeGuardResult(False, "trace", phase, repaired, tuple(), (str(exc),))


def guard_state(state: Mapping[str, Any], *, phase: str = "validate", strict: bool = False, ensure_trace: bool = True) -> RuntimeGuardResult:
    """Validate a Foundation-04.4 state and optional Foundation-04.5 trace at runtime."""
    if phase not in VALID_GUARD_PHASES:
        raise NTPERuntimeGuardError(f"invalid guard phase: {phase}")
    try:
        validation = validate_pipeline_state(_as_mapping(state, "state"))
        normalized = deepcopy(validation.state)
        warnings = list(_collect_warnings(validation))

        if "payload" in normalized:
            payload_result = guard_payload(normalized["payload"], phase=phase, strict=strict)
            normalized["payload"] = payload_result.data
            warnings.extend(payload_result.warnings)

        if ensure_trace:
            normalized = attach_trace_to_state(normalized, normalized.get("execution_trace"))
            trace_result = guard_trace(normalized["execution_trace"], phase=phase, strict=strict)
            normalized["execution_trace"] = _guard_event(trace_result.data, phase, "state", ok=True)
            warnings.extend(trace_result.warnings)

        if "runtime" in normalized and isinstance(normalized["runtime"], Mapping):
            normalized["runtime"]["updated_at"] = utc_now_iso()

        return RuntimeGuardResult(True, "state", phase, normalize_pipeline_state(normalized), tuple(warnings), tuple())
    except Exception as exc:
        if strict:
            raise NTPERuntimeGuardError(f"state guard failed: {exc}") from exc
        repaired = normalize_pipeline_state(_as_mapping(state, "state"))
        if ensure_trace:
            repaired = attach_trace_to_state(repaired, repaired.get("execution_trace"))
            repaired["execution_trace"] = _guard_event(repaired["execution_trace"], phase, "state", ok=False, message=str(exc))
        return RuntimeGuardResult(False, "state", phase, repaired, tuple(), (str(exc),))


def guard_runtime(runtime: Mapping[str, Any], *, phase: str = "validate", strict: bool = False) -> RuntimeGuardResult:
    """Validate the composite runtime object: state, payload, and execution_trace."""
    if phase not in VALID_GUARD_PHASES:
        raise NTPERuntimeGuardError(f"invalid guard phase: {phase}")
    data = _as_mapping(runtime, "runtime")
    state_source = data.get("state") or data
    result = guard_state(state_source, phase=phase, strict=strict, ensure_trace=True)
    guarded = deepcopy(data)
    guarded["state"] = result.data
    guarded["payload"] = result.data.get("payload", guarded.get("payload"))
    guarded["execution_trace"] = result.data.get("execution_trace")
    return RuntimeGuardResult(result.ok, "runtime", phase, guarded, result.warnings, result.errors)


def guard_before_stage(state: Mapping[str, Any], stage: str, *, strict: bool = False) -> Dict[str, Any]:
    """Run guard before a stage executes and append a trace event."""
    result = guard_state(state, phase="before", strict=strict, ensure_trace=True)
    guarded = result.data
    guarded["current_stage"] = stage
    guarded["status"] = "running"
    guarded["execution_trace"] = append_trace_event(
        guarded["execution_trace"],
        "stage",
        "running",
        name=stage,
        message="runtime guard before stage",
        metadata={"guard_version": GUARD_VERSION},
    )
    return normalize_pipeline_state(guarded)


def guard_after_stage(state: Mapping[str, Any], stage: str, *, strict: bool = False) -> Dict[str, Any]:
    """Run guard after a stage executes and append a trace event."""
    result = guard_state(state, phase="after", strict=strict, ensure_trace=True)
    guarded = result.data
    guarded["execution_trace"] = append_trace_event(
        guarded["execution_trace"],
        "stage",
        "validated",
        name=stage,
        message="runtime guard after stage",
        metadata={"guard_version": GUARD_VERSION},
    )
    return normalize_pipeline_state(guarded)


def guard_failure(state: Mapping[str, Any], stage: str, error: Any, *, strict: bool = False) -> Dict[str, Any]:
    """Attach a runtime guard failure to state and execution trace."""
    result = guard_state(state, phase="failed", strict=False, ensure_trace=True)
    guarded = result.data
    guarded["status"] = "failed"
    guarded["current_stage"] = stage
    if stage not in guarded.get("failed_stages", []):
        guarded.setdefault("failed_stages", []).append(stage)
    guarded.setdefault("errors", []).append({"stage": stage, "message": str(error), "time": utc_now_iso(), "source": "runtime_guard"})
    guarded["execution_trace"] = append_trace_event(
        guarded["execution_trace"],
        "error",
        "failed",
        name=stage,
        message=str(error),
        metadata={"guard_version": GUARD_VERSION},
    )
    normalized = normalize_pipeline_state(guarded)
    if strict:
        raise NTPERuntimeGuardError(str(error))
    return normalized


def guarded_call(
    state: Mapping[str, Any],
    stage: str,
    fn: Callable[[Dict[str, Any]], Mapping[str, Any]],
    *,
    strict: bool = False,
) -> Dict[str, Any]:
    """Execute a stage function with before/after/failure runtime guards."""
    guarded = guard_before_stage(state, stage, strict=strict)
    try:
        output = fn(deepcopy(guarded))
        if not isinstance(output, Mapping):
            raise NTPERuntimeGuardError("guarded stage must return a mapping state")
        return guard_after_stage(output, stage, strict=strict)
    except Exception as exc:
        return guard_failure(guarded, stage, exc, strict=strict)
