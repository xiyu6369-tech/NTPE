"""
NTPE Foundation-04.9
Pipeline Recovery Executor

Incremental module. It builds on retry policy contracts without replacing
existing pipeline, adapter, guard, state, trace, or recovery modules.

Purpose:
- Execute a callable with standardized retry/fallback/abort behavior.
- Preserve payload/state/trace contracts while recording recovery decisions.
- Provide a small adapter for production pipeline integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple
import time
import traceback

try:
    from core.pipeline.retry_policy_contract import (
        normalize_retry_policy,
        decide_retry_policy,
        attach_retry_policy,
        attach_retry_decision,
        attach_retry_trace,
    )
except Exception:  # pragma: no cover - keeps direct-file test compatibility
    from retry_policy_contract import (  # type: ignore
        normalize_retry_policy,
        decide_retry_policy,
        attach_retry_policy,
        attach_retry_decision,
        attach_retry_trace,
    )


RECOVERY_EXECUTOR_STATUS = {
    "completed",
    "retrying",
    "fallback_completed",
    "fallback_failed",
    "aborted",
    "failed",
}


@dataclass
class RecoveryExecutionResult:
    status: str
    output: Any = None
    attempts: int = 0
    used_fallback: bool = False
    last_error: Optional[Dict[str, Any]] = None
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    trace: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


def _now() -> float:
    return time.time()


def normalize_execution_result(result: Any) -> Dict[str, Any]:
    if isinstance(result, RecoveryExecutionResult):
        data = asdict(result)
    elif isinstance(result, dict):
        data = dict(result)
    else:
        data = {"status": "completed", "output": result}

    data.setdefault("status", "failed")
    if data["status"] not in RECOVERY_EXECUTOR_STATUS:
        data["status"] = "failed"
    data["attempts"] = max(0, int(data.get("attempts", 0)))
    data["used_fallback"] = bool(data.get("used_fallback", False))
    data["decisions"] = list(data.get("decisions") or [])
    data["state"] = dict(data.get("state") or {})
    data["trace"] = dict(data.get("trace") or {})
    data["metadata"] = dict(data.get("metadata") or {})
    return data


def validate_execution_result(result: Any) -> bool:
    data = normalize_execution_result(result)
    return data["status"] in RECOVERY_EXECUTOR_STATUS and data["attempts"] >= 0


def create_error_record(exc: BaseException, attempt: int = 1, category: Optional[str] = None) -> Dict[str, Any]:
    name = exc.__class__.__name__
    message = str(exc)
    lowered = message.lower()

    if category:
        detected = category
    elif "timeout" in lowered or name.lower().endswith("timeout"):
        detected = "timeout"
    elif "rate" in lowered or "429" in lowered:
        detected = "rate_limit"
    elif "quality" in lowered:
        detected = "quality_failed"
    elif "contract" in lowered or "invalid payload" in lowered:
        detected = "contract_violation"
    elif "fatal" in lowered:
        detected = "fatal"
    else:
        detected = "temporary"

    return {
        "type": name,
        "message": message,
        "reason": message or name,
        "category": detected,
        "attempt": max(1, int(attempt)),
        "timestamp": _now(),
        "traceback": traceback.format_exc(limit=5),
    }


def append_executor_event(trace: Optional[Dict[str, Any]], event_type: str, **payload: Any) -> Dict[str, Any]:
    trace = dict(trace or {})
    events = list(trace.get("events") or [])
    event = {"type": event_type, "timestamp": _now()}
    event.update(payload)
    events.append(event)
    trace["events"] = events
    return trace


def prepare_execution_state(state: Optional[Dict[str, Any]] = None, policy: Optional[Any] = None) -> Dict[str, Any]:
    state = dict(state or {})
    state.setdefault("status", "ready")
    state.setdefault("attempt", 1)
    state.setdefault("recovery_history", [])
    state.setdefault("trace", {"events": []})
    state = attach_retry_policy(state, normalize_retry_policy(policy or state.get("retry_policy")))
    state["trace"] = append_executor_event(state.get("trace"), "recovery_executor_ready", attempt=state["attempt"])
    return state


def _call_with_optional_payload(fn: Callable[..., Any], payload: Any, state: Dict[str, Any]) -> Any:
    try:
        return fn(payload, state)
    except TypeError as exc:
        # Backward compatibility for older callables that only accept payload.
        try:
            return fn(payload)
        except TypeError:
            raise exc


def execute_with_recovery(
    operation: Callable[..., Any],
    payload: Any,
    *,
    state: Optional[Dict[str, Any]] = None,
    policy: Optional[Any] = None,
    fallback: Optional[Callable[..., Any]] = None,
    sleep_enabled: bool = False,
) -> Dict[str, Any]:
    """Execute operation under standardized retry/fallback/abort policy."""

    active_state = prepare_execution_state(state, policy)
    active_policy = active_state["retry_policy"]
    decisions: List[Dict[str, Any]] = []
    attempts = 0
    last_error: Optional[Dict[str, Any]] = None

    while True:
        attempt = max(1, int(active_state.get("attempt", 1)))
        attempts = max(attempts, attempt)
        active_state["status"] = "running"
        active_state["trace"] = append_executor_event(active_state.get("trace"), "recovery_executor_attempt", attempt=attempt)

        try:
            output = _call_with_optional_payload(operation, payload, active_state)
            active_state["status"] = "completed"
            active_state["attempt"] = attempt
            active_state["trace"] = append_executor_event(active_state.get("trace"), "recovery_executor_completed", attempt=attempt)
            return normalize_execution_result(RecoveryExecutionResult(
                status="completed",
                output=output,
                attempts=attempt,
                used_fallback=False,
                last_error=last_error,
                decisions=decisions,
                state=active_state,
                trace=active_state.get("trace", {}),
                metadata={"executor": "foundation_04_9"},
            ))
        except BaseException as exc:
            last_error = create_error_record(exc, attempt=attempt)
            active_state["last_error"] = last_error
            active_state["recovery_history"] = list(active_state.get("recovery_history") or []) + [last_error]
            active_state["trace"] = append_executor_event(active_state.get("trace"), "recovery_executor_error", attempt=attempt, error=last_error)

            decision = decide_retry_policy(last_error, active_policy, attempt=attempt)
            decisions.append(decision)
            active_state = attach_retry_decision(active_state, decision)
            active_state["trace"] = attach_retry_trace(active_state.get("trace", {}), decision)

            action = decision["action"]
            if action == "retry":
                active_state["status"] = "retrying"
                active_state["attempt"] = attempt + 1
                active_state["trace"] = append_executor_event(active_state.get("trace"), "recovery_executor_retry", attempt=attempt, next_attempt=attempt + 1)
                if sleep_enabled and decision.get("delay_seconds", 0) > 0:
                    time.sleep(float(decision["delay_seconds"]))
                continue

            if action == "fallback" and fallback is not None:
                active_state["status"] = "fallback_running"
                active_state["trace"] = append_executor_event(active_state.get("trace"), "recovery_executor_fallback", attempt=attempt)
                try:
                    output = _call_with_optional_payload(fallback, payload, active_state)
                    active_state["status"] = "fallback_completed"
                    active_state["trace"] = append_executor_event(active_state.get("trace"), "recovery_executor_fallback_completed", attempt=attempt)
                    return normalize_execution_result(RecoveryExecutionResult(
                        status="fallback_completed",
                        output=output,
                        attempts=attempt,
                        used_fallback=True,
                        last_error=last_error,
                        decisions=decisions,
                        state=active_state,
                        trace=active_state.get("trace", {}),
                        metadata={"executor": "foundation_04_9"},
                    ))
                except BaseException as fallback_exc:
                    last_error = create_error_record(fallback_exc, attempt=attempt, category="fallback_failed")
                    active_state["last_error"] = last_error
                    active_state["status"] = "fallback_failed"
                    active_state["trace"] = append_executor_event(active_state.get("trace"), "recovery_executor_fallback_failed", attempt=attempt, error=last_error)
                    return normalize_execution_result(RecoveryExecutionResult(
                        status="fallback_failed",
                        output=None,
                        attempts=attempt,
                        used_fallback=True,
                        last_error=last_error,
                        decisions=decisions,
                        state=active_state,
                        trace=active_state.get("trace", {}),
                        metadata={"executor": "foundation_04_9"},
                    ))

            active_state["status"] = "aborted" if action == "abort" else "failed"
            active_state["trace"] = append_executor_event(active_state.get("trace"), "recovery_executor_abort", attempt=attempt, action=action)
            return normalize_execution_result(RecoveryExecutionResult(
                status=active_state["status"],
                output=None,
                attempts=attempt,
                used_fallback=False,
                last_error=last_error,
                decisions=decisions,
                state=active_state,
                trace=active_state.get("trace", {}),
                metadata={"executor": "foundation_04_9"},
            ))


class RecoveryExecutorAdapter:
    """Adapter wrapper for existing production pipeline adapter registries."""

    name = "recovery_executor_adapter"

    def __init__(self, policy: Optional[Any] = None, fallback: Optional[Callable[..., Any]] = None):
        self.policy = normalize_retry_policy(policy)
        self.fallback = fallback

    def before(self, payload: Dict[str, Any], state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = attach_retry_policy(dict(payload or {}), self.policy)
        if state is not None:
            state.update(prepare_execution_state(state, self.policy))
        return payload

    def execute(self, operation: Callable[..., Any], payload: Any, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return execute_with_recovery(operation, payload, state=state, policy=self.policy, fallback=self.fallback)

    def after(self, payload: Dict[str, Any], state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if state is not None:
            state["trace"] = append_executor_event(state.get("trace"), "recovery_executor_adapter_after")
        return payload
