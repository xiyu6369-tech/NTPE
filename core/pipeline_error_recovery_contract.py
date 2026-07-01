"""
NTPE Foundation-04.7
Pipeline Error Recovery Contract

Additive recovery contract for Foundation-04.6 Runtime Guard.

Design goals:
- Do not replace payload/state/trace/runtime guard contracts.
- Convert runtime/stage/plugin/adapter failures into stable recovery results.
- Support retry, fallback, skip, abort, and escalate decisions.
- Preserve unknown/custom fields for forward compatibility.
- Provide deterministic state + trace attachment for Production Pipeline.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

try:
    from core.pipeline_state_contract import normalize_pipeline_state, utc_now_iso
except Exception:  # pragma: no cover
    from datetime import datetime, timezone

    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def normalize_pipeline_state(state: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        data = deepcopy(dict(state or {}))
        data.setdefault("status", "initialized")
        data.setdefault("current_stage", None)
        data.setdefault("completed_stages", [])
        data.setdefault("failed_stages", [])
        data.setdefault("errors", [])
        data.setdefault("warnings", [])
        data.setdefault("counters", {"error_count": len(data.get("errors", [])), "warning_count": len(data.get("warnings", []))})
        data.setdefault("runtime", {"started_at": None, "updated_at": utc_now_iso(), "completed_at": None})
        return data

try:
    from core.pipeline_execution_trace import append_trace_event, attach_trace_to_state, create_execution_trace, normalize_execution_trace
except Exception:  # pragma: no cover
    def create_execution_trace(*, trace_id: Optional[str] = None) -> Dict[str, Any]:
        return {"trace_version": "04.5", "trace_id": trace_id or "ntpe-trace-fallback", "events": [], "summary": {}, "runtime": {"created_at": utc_now_iso(), "updated_at": utc_now_iso(), "completed_at": None}}

    def normalize_execution_trace(trace: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        data = deepcopy(dict(trace or create_execution_trace()))
        data.setdefault("events", [])
        data.setdefault("summary", {})
        data["summary"]["event_count"] = len(data["events"])
        data["summary"]["error_event_count"] = sum(1 for e in data["events"] if e.get("type") == "error" or e.get("status") == "failed")
        return data

    def append_trace_event(trace: Mapping[str, Any], event_type: str, status: str, *, name: Optional[str] = None, message: str = "", metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        data = normalize_execution_trace(trace)
        data["events"].append({"type": event_type, "status": status, "name": name, "message": message, "time": utc_now_iso(), "metadata": dict(metadata or {})})
        return normalize_execution_trace(data)

    def attach_trace_to_state(state: Mapping[str, Any], trace: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        data = normalize_pipeline_state(state)
        data["execution_trace"] = normalize_execution_trace(trace or data.get("execution_trace") or create_execution_trace())
        return data

try:
    from core.pipeline_runtime_guard import guard_state, guard_failure, guarded_call
except Exception:  # pragma: no cover
    def guard_state(state: Mapping[str, Any], *, phase: str = "validate", strict: bool = False, ensure_trace: bool = True):
        class _Result:
            pass
        result = _Result()
        result.ok = True
        result.data = normalize_pipeline_state(state)
        if ensure_trace:
            result.data = attach_trace_to_state(result.data, result.data.get("execution_trace"))
        result.warnings = tuple()
        result.errors = tuple()
        return result

    def guard_failure(state: Mapping[str, Any], stage: str, error: Any, *, strict: bool = False) -> Dict[str, Any]:
        data = normalize_pipeline_state(state)
        data["status"] = "failed"
        data["current_stage"] = stage
        data.setdefault("errors", []).append({"stage": stage, "message": str(error), "time": utc_now_iso(), "source": "runtime_guard"})
        data = attach_trace_to_state(data, data.get("execution_trace"))
        return data

    def guarded_call(state: Mapping[str, Any], stage: str, fn: Callable[[Dict[str, Any]], Mapping[str, Any]], *, strict: bool = False) -> Dict[str, Any]:
        try:
            return normalize_pipeline_state(fn(normalize_pipeline_state(state)))
        except Exception as exc:
            return guard_failure(state, stage, exc, strict=strict)


RECOVERY_VERSION = "04.7"
VALID_RECOVERY_ACTIONS = {"retry", "fallback", "skip", "abort", "escalate", "none"}
VALID_RECOVERY_STATUS = {"pending", "applied", "failed", "exhausted", "skipped", "aborted"}
RETRYABLE_ERROR_HINTS = (
    "timeout",
    "rate limit",
    "429",
    "503",
    "bad gateway",
    "connection",
    "temporar",
    "transient",
)
NON_RETRYABLE_ERROR_HINTS = (
    "invalid payload",
    "invalid status",
    "schema",
    "contract",
    "permission",
    "auth",
    "401",
    "403",
)


class NTPERecoveryError(Exception):
    """Raised when recovery contract validation or execution fails."""


@dataclass(frozen=True)
class RecoveryResult:
    ok: bool
    action: str
    status: str
    state: Dict[str, Any]
    recovery: Dict[str, Any]
    warnings: Tuple[str, ...] = field(default_factory=tuple)
    errors: Tuple[str, ...] = field(default_factory=tuple)


def _as_mapping(value: Any, key: str) -> Dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise NTPERecoveryError(f"{key} must be a mapping")
    return deepcopy(dict(value))


def _as_list(value: Any, key: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise NTPERecoveryError(f"{key} must be a list")
    return deepcopy(value)


def _error_message(error: Any) -> str:
    if isinstance(error, Mapping):
        return str(error.get("message") or error.get("error") or error)
    return str(error)


def _error_type(error: Any) -> str:
    if isinstance(error, Mapping):
        return str(error.get("type") or error.get("error_type") or error.get("source") or "runtime")
    return error.__class__.__name__ if isinstance(error, BaseException) else "runtime"


def create_recovery_record(
    *,
    stage: Optional[str] = None,
    error: Any = None,
    action: str = "retry",
    status: str = "pending",
    attempt: int = 0,
    max_attempts: int = 3,
    fallback_stage: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a stable Foundation-04.7 recovery record."""
    if action not in VALID_RECOVERY_ACTIONS:
        raise NTPERecoveryError(f"invalid recovery action: {action}")
    if status not in VALID_RECOVERY_STATUS:
        raise NTPERecoveryError(f"invalid recovery status: {status}")
    now = utc_now_iso()
    return {
        "recovery_version": RECOVERY_VERSION,
        "stage": stage,
        "action": action,
        "status": status,
        "attempt": int(attempt),
        "max_attempts": int(max_attempts),
        "fallback_stage": fallback_stage,
        "error": {
            "type": _error_type(error),
            "message": _error_message(error),
            "time": now,
        },
        "metadata": dict(metadata or {}),
        "runtime": {
            "created_at": now,
            "updated_at": now,
            "applied_at": None,
        },
    }


def normalize_recovery_record(record: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Normalize legacy/minimal recovery data into the Foundation-04.7 shape."""
    incoming = deepcopy(dict(record or {}))
    if "action" not in incoming and "decision" in incoming:
        incoming["action"] = incoming.get("decision")
    if "attempt" not in incoming and "retry_count" in incoming:
        incoming["attempt"] = incoming.get("retry_count")

    base = create_recovery_record(
        stage=incoming.get("stage"),
        error=incoming.get("error"),
        action=str(incoming.get("action") or "retry"),
        status=str(incoming.get("status") or "pending"),
        attempt=int(incoming.get("attempt") or 0),
        max_attempts=int(incoming.get("max_attempts") or 3),
        fallback_stage=incoming.get("fallback_stage"),
        metadata=incoming.get("metadata") if isinstance(incoming.get("metadata"), Mapping) else None,
    )

    for key, value in incoming.items():
        if key == "error":
            error = _as_mapping(value, "error")
            merged = deepcopy(base["error"])
            merged.update(error)
            base["error"] = merged
        elif key == "metadata":
            base["metadata"] = _as_mapping(value, "metadata")
        elif key == "runtime":
            runtime = deepcopy(base["runtime"])
            runtime.update(_as_mapping(value, "runtime"))
            base["runtime"] = runtime
        else:
            base[key] = deepcopy(value)

    if base["action"] not in VALID_RECOVERY_ACTIONS:
        raise NTPERecoveryError(f"invalid recovery action: {base['action']}")
    if base["status"] not in VALID_RECOVERY_STATUS:
        raise NTPERecoveryError(f"invalid recovery status: {base['status']}")
    base["attempt"] = int(base.get("attempt") or 0)
    base["max_attempts"] = int(base.get("max_attempts") or 0)
    base["runtime"]["updated_at"] = utc_now_iso()
    return base


def validate_recovery_record(record: Mapping[str, Any]) -> RecoveryResult:
    """Validate recovery record and return a neutral result without applying it."""
    normalized = normalize_recovery_record(record)
    state = normalize_pipeline_state({"status": "initialized"})
    warnings: list[str] = []
    if normalized["action"] == "retry" and normalized["max_attempts"] <= 0:
        warnings.append("retry action has non-positive max_attempts")
    if normalized["attempt"] > normalized["max_attempts"]:
        warnings.append("recovery attempt exceeds max_attempts")
    return RecoveryResult(True, normalized["action"], normalized["status"], state, normalized, tuple(warnings), tuple())


def classify_recovery_action(error: Any, *, attempt: int = 0, max_attempts: int = 3, fallback_available: bool = False) -> str:
    """Choose a deterministic recovery action from error text and retry budget."""
    message = _error_message(error).lower()
    if any(hint in message for hint in NON_RETRYABLE_ERROR_HINTS):
        return "abort"
    if fallback_available and attempt >= max_attempts:
        return "fallback"
    if any(hint in message for hint in RETRYABLE_ERROR_HINTS) and attempt < max_attempts:
        return "retry"
    if attempt < max_attempts and not message:
        return "retry"
    if fallback_available:
        return "fallback"
    return "abort"


def attach_recovery_to_state(state: Mapping[str, Any], recovery: Mapping[str, Any]) -> Dict[str, Any]:
    """Attach a recovery record to pipeline state and execution trace."""
    guarded = guard_state(state, phase="validate", strict=False, ensure_trace=True).data
    record = normalize_recovery_record(recovery)
    guarded.setdefault("recovery", {})
    history = _as_list(guarded["recovery"].get("history"), "recovery.history")
    history.append(record)
    guarded["recovery"] = {
        **deepcopy(guarded.get("recovery") or {}),
        "current": record,
        "history": history,
        "summary": {
            "recovery_count": len(history),
            "retry_count": sum(1 for item in history if item.get("action") == "retry"),
            "fallback_count": sum(1 for item in history if item.get("action") == "fallback"),
            "abort_count": sum(1 for item in history if item.get("action") == "abort"),
        },
    }
    trace_status_map = {
        "pending": "running",
        "applied": "applied",
        "failed": "failed",
        "exhausted": "failed",
        "skipped": "skipped",
        "aborted": "failed",
    }
    guarded["execution_trace"] = append_trace_event(
        guarded["execution_trace"],
        "error" if record["action"] in {"abort", "escalate"} or record["status"] in {"failed", "exhausted", "aborted"} else "trace",
        trace_status_map.get(record["status"], "running"),
        name=f"recovery:{record['action']}:{record.get('stage')}",
        message=record["error"].get("message", ""),
        metadata={"recovery_version": RECOVERY_VERSION, "action": record["action"], "recovery_status": record["status"], "attempt": record["attempt"], "max_attempts": record["max_attempts"]},
    )
    guarded["runtime"]["updated_at"] = utc_now_iso()
    return normalize_pipeline_state(guarded)


def plan_recovery(
    state: Mapping[str, Any],
    stage: str,
    error: Any,
    *,
    attempt: int = 0,
    max_attempts: int = 3,
    fallback_stage: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> RecoveryResult:
    """Create and attach a pending recovery decision to state."""
    action = classify_recovery_action(error, attempt=attempt, max_attempts=max_attempts, fallback_available=fallback_stage is not None)
    record = create_recovery_record(
        stage=stage,
        error=error,
        action=action,
        status="pending",
        attempt=attempt,
        max_attempts=max_attempts,
        fallback_stage=fallback_stage,
        metadata=metadata,
    )
    planned_state = attach_recovery_to_state(state, record)
    return RecoveryResult(True, action, "pending", planned_state, record, tuple(), tuple())


def mark_recovery_applied(state: Mapping[str, Any], recovery: Optional[Mapping[str, Any]] = None, *, status: str = "applied") -> Dict[str, Any]:
    """Mark current recovery as applied/skipped/aborted/exhausted and append trace."""
    if status not in VALID_RECOVERY_STATUS:
        raise NTPERecoveryError(f"invalid recovery status: {status}")
    guarded = guard_state(state, phase="validate", strict=False, ensure_trace=True).data
    record = normalize_recovery_record(recovery or (guarded.get("recovery") or {}).get("current") or {})
    record["status"] = status
    record["runtime"]["updated_at"] = utc_now_iso()
    record["runtime"]["applied_at"] = record["runtime"]["updated_at"]
    guarded = attach_recovery_to_state(guarded, record)
    if record["action"] == "abort" or status == "aborted":
        guarded["status"] = "failed"
    elif record["action"] == "skip" or status == "skipped":
        guarded["status"] = "skipped"
    else:
        guarded["status"] = "running"
    return normalize_pipeline_state(guarded)


def apply_recovery(
    state: Mapping[str, Any],
    recovery: Optional[Mapping[str, Any]] = None,
    *,
    retry_fn: Optional[Callable[[Dict[str, Any]], Mapping[str, Any]]] = None,
    fallback_fn: Optional[Callable[[Dict[str, Any]], Mapping[str, Any]]] = None,
    strict: bool = False,
) -> RecoveryResult:
    """Apply a recovery action using optional retry/fallback callables."""
    guarded = guard_state(state, phase="validate", strict=False, ensure_trace=True).data
    record = normalize_recovery_record(recovery or (guarded.get("recovery") or {}).get("current") or {})
    action = record["action"]
    stage = str(record.get("stage") or guarded.get("current_stage") or "recovery")

    try:
        if action == "retry":
            if record["attempt"] >= record["max_attempts"]:
                exhausted = deepcopy(record)
                exhausted["status"] = "exhausted"
                new_state = mark_recovery_applied(guarded, exhausted, status="exhausted")
                return RecoveryResult(False, action, "exhausted", new_state, exhausted, tuple(), ("retry attempts exhausted",))
            if retry_fn is None:
                raise NTPERecoveryError("retry_fn is required for retry recovery")
            next_record = deepcopy(record)
            next_record["attempt"] = int(next_record["attempt"]) + 1
            new_state = guarded_call(mark_recovery_applied(guarded, next_record), stage, retry_fn, strict=strict)
            return RecoveryResult(new_state.get("status") != "failed", action, "applied", new_state, next_record, tuple(), tuple())

        if action == "fallback":
            if fallback_fn is None:
                raise NTPERecoveryError("fallback_fn is required for fallback recovery")
            fallback_stage = str(record.get("fallback_stage") or f"{stage}:fallback")
            new_state = guarded_call(mark_recovery_applied(guarded, record), fallback_stage, fallback_fn, strict=strict)
            return RecoveryResult(new_state.get("status") != "failed", action, "applied", new_state, record, tuple(), tuple())

        if action == "skip":
            new_state = mark_recovery_applied(guarded, record, status="skipped")
            return RecoveryResult(True, action, "skipped", new_state, record, tuple(), tuple())

        if action == "abort":
            failed_state = guard_failure(guarded, stage, record["error"].get("message"), strict=False)
            new_state = mark_recovery_applied(failed_state, record, status="aborted")
            return RecoveryResult(False, action, "aborted", new_state, record, tuple(), (record["error"].get("message", ""),))

        if action == "escalate":
            failed_state = guard_failure(guarded, stage, record["error"].get("message"), strict=False)
            new_state = mark_recovery_applied(failed_state, record, status="aborted")
            return RecoveryResult(False, action, "aborted", new_state, record, tuple(), ("escalated",))

        new_state = mark_recovery_applied(guarded, record, status="applied")
        return RecoveryResult(True, action, "applied", new_state, record, tuple(), tuple())
    except Exception as exc:
        failed = guard_failure(guarded, stage, exc, strict=False)
        if strict:
            raise NTPERecoveryError(str(exc)) from exc
        return RecoveryResult(False, action, "failed", failed, record, tuple(), (str(exc),))


def recover_call(
    state: Mapping[str, Any],
    stage: str,
    fn: Callable[[Dict[str, Any]], Mapping[str, Any]],
    *,
    fallback_fn: Optional[Callable[[Dict[str, Any]], Mapping[str, Any]]] = None,
    max_attempts: int = 3,
    strict: bool = False,
) -> Dict[str, Any]:
    """Execute a guarded stage and apply retry/fallback recovery if it fails."""
    current = guard_state(state, phase="validate", strict=False, ensure_trace=True).data
    last_error: Any = None

    for attempt in range(0, max_attempts + 1):
        result_state = guarded_call(current, stage, fn, strict=False)
        if result_state.get("status") != "failed":
            return result_state
        last_error = (result_state.get("errors") or [{"message": "stage failed"}])[-1]
        plan = plan_recovery(
            result_state,
            stage,
            last_error,
            attempt=attempt,
            max_attempts=max_attempts,
            fallback_stage=f"{stage}:fallback" if fallback_fn else None,
        )
        if plan.action != "retry":
            return apply_recovery(plan.state, plan.recovery, fallback_fn=fallback_fn, strict=strict).state
        if attempt >= max_attempts:
            return apply_recovery(plan.state, plan.recovery, retry_fn=fn, fallback_fn=fallback_fn, strict=strict).state
        current = mark_recovery_applied(plan.state, plan.recovery, status="applied")

    final_plan = plan_recovery(current, stage, last_error or "stage failed", attempt=max_attempts, max_attempts=max_attempts, fallback_stage=f"{stage}:fallback" if fallback_fn else None)
    return apply_recovery(final_plan.state, final_plan.recovery, fallback_fn=fallback_fn, strict=strict).state
