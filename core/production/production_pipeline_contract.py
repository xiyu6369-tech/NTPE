"""
NTPE Foundation-05.0
Production Pipeline Contract Integration

This module is intentionally additive.  It does not replace any Foundation-04.x
contracts.  It provides a stable integration surface for production pipeline
execution while tolerating older project layouts through local compatibility
helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, MutableMapping, Optional
import traceback
import uuid


PipelineStage = Callable[[Dict[str, Any], Dict[str, Any]], Any]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _ensure_dict(value: Any, *, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {} if default is None else dict(default)


def _ensure_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _normalize_payload(payload: Any) -> Dict[str, Any]:
    """Normalize legacy payloads without requiring a hard dependency."""
    if isinstance(payload, dict):
        normalized = dict(payload)
    else:
        normalized = {"source": payload}

    normalized.setdefault("payload_id", _make_id("payload"))
    normalized.setdefault("source", "")
    normalized.setdefault("target_language", "zh-TW")
    normalized.setdefault("context", {})
    normalized.setdefault("metadata", {})
    normalized.setdefault("created_at", _now())
    return normalized


def _create_state(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "state_id": _make_id("state"),
        "status": "created",
        "current_stage": None,
        "payload": payload,
        "counters": {
            "stages_started": 0,
            "stages_completed": 0,
            "failures": 0,
            "recoveries": 0,
        },
        "events": [],
        "created_at": _now(),
        "updated_at": _now(),
    }


def _create_trace() -> Dict[str, Any]:
    return {
        "trace_id": _make_id("trace"),
        "events": [],
        "summary": {
            "stage_events": 0,
            "plugin_events": 0,
            "adapter_events": 0,
            "failure_events": 0,
            "production_events": 0,
        },
        "created_at": _now(),
        "updated_at": _now(),
    }


def _trace_event(trace: Dict[str, Any], event_type: str, **data: Any) -> Dict[str, Any]:
    event = {
        "event_id": _make_id("event"),
        "type": event_type,
        "timestamp": _now(),
        "data": data,
    }
    trace.setdefault("events", []).append(event)
    summary = trace.setdefault("summary", {})
    if event_type.startswith("stage."):
        summary["stage_events"] = summary.get("stage_events", 0) + 1
    elif event_type.startswith("plugin."):
        summary["plugin_events"] = summary.get("plugin_events", 0) + 1
    elif event_type.startswith("adapter."):
        summary["adapter_events"] = summary.get("adapter_events", 0) + 1
    elif event_type.startswith("failure."):
        summary["failure_events"] = summary.get("failure_events", 0) + 1
    elif event_type.startswith("production."):
        summary["production_events"] = summary.get("production_events", 0) + 1
    trace["updated_at"] = _now()
    return event


def _state_event(state: Dict[str, Any], event_type: str, **data: Any) -> Dict[str, Any]:
    event = {
        "event_id": _make_id("state_event"),
        "type": event_type,
        "timestamp": _now(),
        "data": data,
    }
    state.setdefault("events", []).append(event)
    state["updated_at"] = _now()
    return event


def _default_policy() -> Dict[str, Any]:
    return {
        "policy_id": _make_id("policy"),
        "max_attempts": 2,
        "fallback_enabled": True,
        "abort_on_contract_error": True,
        "created_at": _now(),
    }


def _classify_error(error: BaseException, attempt: int, policy: Dict[str, Any]) -> Dict[str, Any]:
    max_attempts = int(policy.get("max_attempts", 1))
    if attempt < max_attempts:
        action = "retry"
    elif bool(policy.get("fallback_enabled", False)):
        action = "fallback"
    else:
        action = "abort"

    return {
        "decision_id": _make_id("decision"),
        "action": action,
        "attempt": attempt,
        "max_attempts": max_attempts,
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "created_at": _now(),
    }


def _format_error(error: BaseException) -> Dict[str, Any]:
    return {
        "type": error.__class__.__name__,
        "message": str(error),
        "traceback": traceback.format_exc(),
    }


@dataclass
class ProductionPipelineResult:
    """Stable result object for production pipeline execution."""

    status: str
    output: Any = None
    payload: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    trace: Dict[str, Any] = field(default_factory=dict)
    recovery: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "output": self.output,
            "payload": self.payload,
            "state": self.state,
            "trace": self.trace,
            "recovery": self.recovery,
            "metadata": self.metadata,
            "errors": self.errors,
        }


def create_production_pipeline_result(
    *,
    status: str = "created",
    output: Any = None,
    payload: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None,
    trace: Optional[Dict[str, Any]] = None,
    recovery: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    errors: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    result = ProductionPipelineResult(
        status=status,
        output=output,
        payload=_ensure_dict(payload),
        state=_ensure_dict(state),
        trace=_ensure_dict(trace),
        recovery=_ensure_dict(recovery),
        metadata=_ensure_dict(metadata),
        errors=_ensure_list(errors),
    )
    return result.to_dict()


def validate_production_pipeline_result(result: Any) -> bool:
    if not isinstance(result, dict):
        return False
    required = ["status", "payload", "state", "trace", "metadata", "errors"]
    if any(key not in result for key in required):
        return False
    if not isinstance(result.get("payload"), dict):
        return False
    if not isinstance(result.get("state"), dict):
        return False
    if not isinstance(result.get("trace"), dict):
        return False
    if not isinstance(result.get("errors"), list):
        return False
    return result.get("status") in {"created", "running", "completed", "failed", "aborted", "fallback"}


def build_production_pipeline_context(
    payload: Any,
    *,
    policy: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    normalized_payload = _normalize_payload(payload)
    state = _create_state(normalized_payload)
    trace = _create_trace()
    active_policy = dict(_default_policy())
    if policy:
        active_policy.update(policy)

    context = {
        "production_id": _make_id("production"),
        "payload": normalized_payload,
        "state": state,
        "trace": trace,
        "policy": active_policy,
        "metadata": dict(metadata or {}),
        "created_at": _now(),
    }
    state["policy"] = active_policy
    _trace_event(trace, "production.context_created", production_id=context["production_id"])
    _state_event(state, "production.context_created", production_id=context["production_id"])
    return context


def execute_production_pipeline_stage(
    stage_name: str,
    stage: PipelineStage,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    payload = context["payload"]
    state = context["state"]
    trace = context["trace"]
    policy = context.get("policy") or _default_policy()

    state["status"] = "running"
    state["current_stage"] = stage_name
    state.setdefault("counters", {})["stages_started"] = state.get("counters", {}).get("stages_started", 0) + 1
    _trace_event(trace, "stage.begin", stage=stage_name)
    _state_event(state, "stage.begin", stage=stage_name)

    attempt = 1
    while True:
        try:
            _trace_event(trace, "production.stage_attempt", stage=stage_name, attempt=attempt)
            output = stage(payload, context)
            payload["last_output"] = output
            state["status"] = "completed"
            state["current_stage"] = stage_name
            state.setdefault("counters", {})["stages_completed"] = state.get("counters", {}).get("stages_completed", 0) + 1
            _trace_event(trace, "stage.complete", stage=stage_name, attempt=attempt)
            _state_event(state, "stage.complete", stage=stage_name, attempt=attempt)
            return create_production_pipeline_result(
                status="completed",
                output=output,
                payload=payload,
                state=state,
                trace=trace,
                metadata={"stage": stage_name, "attempts": attempt},
            )
        except Exception as exc:  # noqa: BLE001 - contract layer must capture all stage errors
            state.setdefault("counters", {})["failures"] = state.get("counters", {}).get("failures", 0) + 1
            error = _format_error(exc)
            decision = _classify_error(exc, attempt, policy)
            recovery = {
                "recovery_id": _make_id("recovery"),
                "stage": stage_name,
                "decision": decision,
                "error": error,
                "created_at": _now(),
            }
            state["recovery"] = recovery
            _trace_event(trace, "failure.stage", stage=stage_name, attempt=attempt, decision=decision)
            _state_event(state, "failure.stage", stage=stage_name, attempt=attempt, decision=decision)

            if decision["action"] == "retry":
                state.setdefault("counters", {})["recoveries"] = state.get("counters", {}).get("recoveries", 0) + 1
                _trace_event(trace, "production.retry", stage=stage_name, next_attempt=attempt + 1)
                attempt += 1
                continue

            if decision["action"] == "fallback":
                state["status"] = "fallback"
                fallback_output = {
                    "fallback": True,
                    "stage": stage_name,
                    "error": error["message"],
                    "payload": payload,
                }
                _trace_event(trace, "production.fallback", stage=stage_name)
                return create_production_pipeline_result(
                    status="fallback",
                    output=fallback_output,
                    payload=payload,
                    state=state,
                    trace=trace,
                    recovery=recovery,
                    metadata={"stage": stage_name, "attempts": attempt},
                    errors=[error],
                )

            state["status"] = "aborted"
            _trace_event(trace, "production.abort", stage=stage_name)
            return create_production_pipeline_result(
                status="aborted",
                output=None,
                payload=payload,
                state=state,
                trace=trace,
                recovery=recovery,
                metadata={"stage": stage_name, "attempts": attempt},
                errors=[error],
            )


def execute_production_pipeline(
    payload: Any,
    stages: Iterable[tuple[str, PipelineStage]],
    *,
    policy: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context = build_production_pipeline_context(payload, policy=policy, metadata=metadata)
    final_output: Any = None

    for stage_name, stage in stages:
        result = execute_production_pipeline_stage(stage_name, stage, context)
        if result["status"] not in {"completed"}:
            return result
        final_output = result.get("output")

    context["state"]["status"] = "completed"
    _trace_event(context["trace"], "production.complete", production_id=context["production_id"])
    _state_event(context["state"], "production.complete", production_id=context["production_id"])
    return create_production_pipeline_result(
        status="completed",
        output=final_output,
        payload=context["payload"],
        state=context["state"],
        trace=context["trace"],
        metadata={**context.get("metadata", {}), "production_id": context["production_id"]},
    )
