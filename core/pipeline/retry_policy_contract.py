"""
NTPE Foundation-04.8
Pipeline Retry Policy Contract

Incremental module. It does not replace existing recovery/state/trace modules.
It standardizes retry policy objects and policy decisions for production pipeline use.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import time


TERMINAL_ACTIONS = {"retry", "fallback", "abort", "ignore"}
RETRYABLE_CATEGORIES = {"timeout", "rate_limit", "network", "temporary", "guard_recoverable"}
FALLBACK_CATEGORIES = {"model_error", "quality_failed", "adapter_failed", "plugin_failed"}
ABORT_CATEGORIES = {"fatal", "contract_violation", "invalid_payload", "strict_guard_failure"}


@dataclass
class RetryPolicy:
    name: str = "default"
    max_attempts: int = 3
    fallback_after: int = 2
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    backoff_multiplier: float = 2.0
    jitter_seconds: float = 0.0
    retryable_categories: List[str] = field(default_factory=lambda: sorted(RETRYABLE_CATEGORIES))
    fallback_categories: List[str] = field(default_factory=lambda: sorted(FALLBACK_CATEGORIES))
    abort_categories: List[str] = field(default_factory=lambda: sorted(ABORT_CATEGORIES))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryDecision:
    action: str
    attempt: int
    max_attempts: int
    delay_seconds: float = 0.0
    category: str = "temporary"
    reason: str = ""
    policy_name: str = "default"
    should_record_trace: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


def normalize_retry_policy(policy: Optional[Any] = None) -> Dict[str, Any]:
    if policy is None:
        policy = RetryPolicy()
    if isinstance(policy, RetryPolicy):
        data = asdict(policy)
    elif isinstance(policy, dict):
        data = dict(policy)
    else:
        data = {"name": str(policy)}

    default = asdict(RetryPolicy())
    default.update(data)
    default["max_attempts"] = max(1, int(default.get("max_attempts", 3)))
    default["fallback_after"] = max(1, int(default.get("fallback_after", 2)))
    default["base_delay_seconds"] = max(0.0, float(default.get("base_delay_seconds", 1.0)))
    default["max_delay_seconds"] = max(0.0, float(default.get("max_delay_seconds", 30.0)))
    default["backoff_multiplier"] = max(1.0, float(default.get("backoff_multiplier", 2.0)))
    default["jitter_seconds"] = max(0.0, float(default.get("jitter_seconds", 0.0)))
    default["retryable_categories"] = list(default.get("retryable_categories") or [])
    default["fallback_categories"] = list(default.get("fallback_categories") or [])
    default["abort_categories"] = list(default.get("abort_categories") or [])
    default["metadata"] = dict(default.get("metadata") or {})
    return default


def validate_retry_policy(policy: Any) -> bool:
    p = normalize_retry_policy(policy)
    if not p.get("name"):
        return False
    if p["max_attempts"] < 1:
        return False
    if p["fallback_after"] < 1:
        return False
    if p["base_delay_seconds"] < 0 or p["max_delay_seconds"] < 0:
        return False
    if p["backoff_multiplier"] < 1:
        return False
    return True


def calculate_retry_delay(policy: Any, attempt: int) -> float:
    p = normalize_retry_policy(policy)
    attempt = max(1, int(attempt))
    delay = p["base_delay_seconds"] * (p["backoff_multiplier"] ** (attempt - 1))
    delay = min(delay, p["max_delay_seconds"])
    if p["jitter_seconds"]:
        delay += min(p["jitter_seconds"], p["max_delay_seconds"])
    return float(delay)


def normalize_retry_decision(decision: Any) -> Dict[str, Any]:
    if isinstance(decision, RetryDecision):
        data = asdict(decision)
    elif isinstance(decision, dict):
        data = dict(decision)
    else:
        data = {"action": str(decision)}

    default = asdict(RetryDecision(action="abort", attempt=1, max_attempts=1))
    default.update(data)
    if default["action"] not in TERMINAL_ACTIONS:
        default["action"] = "abort"
    default["attempt"] = max(1, int(default.get("attempt", 1)))
    default["max_attempts"] = max(1, int(default.get("max_attempts", 1)))
    default["delay_seconds"] = max(0.0, float(default.get("delay_seconds", 0.0)))
    default["metadata"] = dict(default.get("metadata") or {})
    return default


def validate_retry_decision(decision: Any) -> bool:
    d = normalize_retry_decision(decision)
    return d["action"] in TERMINAL_ACTIONS and d["attempt"] >= 1 and d["max_attempts"] >= 1


def decide_retry_policy(error_record: Optional[Dict[str, Any]], policy: Optional[Any] = None, attempt: int = 1) -> Dict[str, Any]:
    p = normalize_retry_policy(policy)
    record = dict(error_record or {})
    category = record.get("category") or record.get("error_category") or "temporary"
    reason = record.get("reason") or record.get("message") or "policy decision"
    attempt = max(1, int(record.get("attempt", attempt)))

    if category in p["abort_categories"]:
        action = "abort"
        delay = 0.0
    elif attempt >= p["max_attempts"]:
        action = "abort"
        delay = 0.0
    elif category in p["fallback_categories"] and attempt >= p["fallback_after"]:
        action = "fallback"
        delay = 0.0
    elif category in p["retryable_categories"] or category not in p["abort_categories"]:
        action = "retry"
        delay = calculate_retry_delay(p, attempt)
    else:
        action = "abort"
        delay = 0.0

    decision = RetryDecision(
        action=action,
        attempt=attempt,
        max_attempts=p["max_attempts"],
        delay_seconds=delay,
        category=category,
        reason=reason,
        policy_name=p["name"],
        metadata={"source": "retry_policy_contract"},
    )
    return normalize_retry_decision(decision)


def attach_retry_policy(target: Dict[str, Any], policy: Optional[Any] = None) -> Dict[str, Any]:
    target = dict(target or {})
    target["retry_policy"] = normalize_retry_policy(policy)
    return target


def attach_retry_decision(target: Dict[str, Any], decision: Any) -> Dict[str, Any]:
    target = dict(target or {})
    history = list(target.get("retry_decisions") or [])
    normalized = normalize_retry_decision(decision)
    history.append(normalized)
    target["retry_decision"] = normalized
    target["retry_decisions"] = history
    return target


def attach_retry_trace(trace: Dict[str, Any], decision: Any) -> Dict[str, Any]:
    trace = dict(trace or {})
    events = list(trace.get("events") or [])
    events.append({
        "type": "retry_policy_decision",
        "timestamp": time.time(),
        "decision": normalize_retry_decision(decision),
    })
    trace["events"] = events
    return trace


def apply_retry_policy(error_record: Optional[Dict[str, Any]], state: Optional[Dict[str, Any]] = None, policy: Optional[Any] = None) -> Dict[str, Any]:
    state = dict(state or {})
    policy_data = normalize_retry_policy(policy or state.get("retry_policy"))
    attempt = int((error_record or {}).get("attempt", state.get("attempt", 1)))
    decision = decide_retry_policy(error_record, policy_data, attempt=attempt)
    state = attach_retry_policy(state, policy_data)
    state = attach_retry_decision(state, decision)
    if decision["action"] == "retry":
        state["status"] = "retry_scheduled"
        state["attempt"] = decision["attempt"] + 1
    elif decision["action"] == "fallback":
        state["status"] = "fallback_scheduled"
    elif decision["action"] == "abort":
        state["status"] = "aborted"
    else:
        state["status"] = "ignored"
    if "trace" in state:
        state["trace"] = attach_retry_trace(state["trace"], decision)
    return state


class RetryPolicyAdapter:
    """Small adapter wrapper for existing pipeline adapter registries."""

    name = "retry_policy_adapter"

    def __init__(self, policy: Optional[Any] = None):
        self.policy = normalize_retry_policy(policy)

    def before(self, payload: Dict[str, Any], state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = attach_retry_policy(payload, self.policy)
        if state is not None:
            state["retry_policy"] = self.policy
        return payload

    def after(self, payload: Dict[str, Any], state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if state is not None and state.get("last_error"):
            new_state = apply_retry_policy(state.get("last_error"), state, self.policy)
            state.clear()
            state.update(new_state)
        return payload
