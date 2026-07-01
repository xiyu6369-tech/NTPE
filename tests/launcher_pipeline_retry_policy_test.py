import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.pipeline.retry_policy_contract import (
    RetryPolicy,
    RetryPolicyAdapter,
    normalize_retry_policy,
    validate_retry_policy,
    calculate_retry_delay,
    decide_retry_policy,
    normalize_retry_decision,
    validate_retry_decision,
    attach_retry_policy,
    attach_retry_decision,
    attach_retry_trace,
    apply_retry_policy,
)


def check(name, cond):
    print(f"{name:<24} {'PASS' if cond else 'FAIL'}")
    if not cond:
        raise AssertionError(name)


def main():
    print("NTPE Foundation-04.8 Pipeline Retry Policy Contract Test")
    print("=" * 56)

    legacy = {"max_attempts": "5", "fallback_after": "3"}
    p = normalize_retry_policy(legacy)
    check("Legacy Policy", p["max_attempts"] == 5)
    check("Policy Created", normalize_retry_policy(RetryPolicy(name="unit"))["name"] == "unit")
    check("Validate Policy", validate_retry_policy(p))
    check("Delay Created", calculate_retry_delay({"base_delay_seconds": 2, "backoff_multiplier": 2}, 3) == 8)

    retry = decide_retry_policy({"category": "timeout", "attempt": 1}, p)
    check("Decision Retry", retry["action"] == "retry")
    check("Decision Delay", retry["delay_seconds"] >= 1)

    fallback = decide_retry_policy({"category": "quality_failed", "attempt": 3}, p)
    check("Decision Fallback", fallback["action"] == "fallback")

    abort = decide_retry_policy({"category": "fatal", "attempt": 1}, p)
    check("Decision Abort", abort["action"] == "abort")

    maxed = decide_retry_policy({"category": "timeout", "attempt": 5}, p)
    check("Decision Max Abort", maxed["action"] == "abort")

    nd = normalize_retry_decision({"action": "retry", "attempt": 1, "max_attempts": 5})
    check("Normalize Decision", nd["action"] == "retry")
    check("Validate Decision", validate_retry_decision(nd))

    target = attach_retry_policy({}, p)
    check("Attach Policy", "retry_policy" in target)
    target = attach_retry_decision(target, retry)
    check("Attach Decision", target["retry_decision"]["action"] == "retry")
    check("Decision History", len(target["retry_decisions"]) == 1)

    trace = attach_retry_trace({"events": []}, retry)
    check("Trace Event", trace["events"][-1]["type"] == "retry_policy_decision")

    state = {"attempt": 1, "trace": {"events": []}}
    state = apply_retry_policy({"category": "timeout", "attempt": 1}, state, p)
    check("Apply Retry", state["status"] == "retry_scheduled")
    check("Retry Attempt", state["attempt"] == 2)
    check("State Trace", state["trace"]["events"])

    state2 = apply_retry_policy({"category": "quality_failed", "attempt": 3}, {"trace": {"events": []}}, p)
    check("Apply Fallback", state2["status"] == "fallback_scheduled")

    state3 = apply_retry_policy({"category": "fatal", "attempt": 1}, {}, p)
    check("Apply Abort", state3["status"] == "aborted")

    adapter = RetryPolicyAdapter(p)
    payload = adapter.before({"source": "x"})
    check("Adapter Before", "retry_policy" in payload)

    st = {"last_error": {"category": "timeout", "attempt": 1}, "trace": {"events": []}}
    payload = adapter.after(payload, st)
    check("Adapter After", st["status"] == "retry_scheduled")
    check("Adapter Trace", st["trace"]["events"])

    print("PASS")


if __name__ == "__main__":
    main()
