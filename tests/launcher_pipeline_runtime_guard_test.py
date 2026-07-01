r"""
NTPE Foundation-04.6 Pipeline Runtime Guard Test
Run:
    python tests\launcher_pipeline_runtime_guard_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.pipeline_execution_trace import create_execution_trace
from core.pipeline_runtime_guard import (
    NTPERuntimeGuardError,
    guard_after_stage,
    guard_before_stage,
    guard_failure,
    guard_payload,
    guard_runtime,
    guard_state,
    guard_trace,
    guarded_call,
)
from core.pipeline_runtime_guard_adapter import PipelineRuntimeGuardAdapter
from core.pipeline_state_contract import create_pipeline_state


def check(label: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"{label:<24} {status}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    print("NTPE Foundation-04.6 Pipeline Runtime Guard Test")
    print("=" * 62)

    payload = {"text": "안녕하세요.", "language": "繁體中文"}
    payload_result = guard_payload(payload)
    check("Payload Guard", payload_result.ok is True)
    check("Payload Normalized", payload_result.data["target_language"] == "繁體中文")

    trace = create_execution_trace(trace_id="guard-trace")
    trace_result = guard_trace(trace)
    check("Trace Guard", trace_result.ok is True)
    check("Trace Preserved", trace_result.data["trace_id"] == "guard-trace")

    state = create_pipeline_state(payload, stage="context")
    state["execution_trace"] = trace
    state_result = guard_state(state)
    check("State Guard", state_result.ok is True)
    check("State Trace", "execution_trace" in state_result.data)
    check("Guard Event", state_result.data["execution_trace"]["events"][-1]["name"].startswith("runtime_guard"))

    runtime_result = guard_runtime({"state": state_result.data})
    check("Runtime Guard", runtime_result.ok is True)
    check("Runtime Payload", runtime_result.data["payload"]["target_language"] == "繁體中文")

    before = guard_before_stage(state_result.data, "prompt")
    check("Before Stage", before["current_stage"] == "prompt")
    check("Before Status", before["status"] == "running")

    after = guard_after_stage(before, "prompt")
    check("After Stage", after["execution_trace"]["events"][-1]["status"] == "validated")

    failed = guard_failure(after, "quality", "quality failed")
    check("Failure Status", failed["status"] == "failed")
    check("Failure Counter", failed["counters"]["error_count"] == 1)

    def good_stage(current_state):
        current_state["custom_stage_output"] = "ok"
        return current_state

    called = guarded_call(state_result.data, "narrative", good_stage)
    check("Guarded Call", called["custom_stage_output"] == "ok")
    check("Call Trace", called["execution_trace"]["events"][-1]["name"] == "narrative")

    def bad_stage(current_state):
        raise RuntimeError("adapter mutated invalid state")

    bad_called = guarded_call(state_result.data, "adapter", bad_stage)
    check("Guarded Failure", bad_called["status"] == "failed")

    strict_failed = False
    try:
        guard_state({"status": "impossible"}, strict=True)
    except NTPERuntimeGuardError:
        strict_failed = True
    check("Strict Failure", strict_failed is True)

    adapter = PipelineRuntimeGuardAdapter()
    adapter_before = adapter.before_stage(state_result.data, "quality")
    adapter_after = adapter.after_stage(adapter_before, "quality")
    adapter_result = adapter.state(adapter_after)
    check("Adapter Before", adapter_before["current_stage"] == "quality")
    check("Adapter After", adapter_after["execution_trace"]["events"][-1]["status"] == "validated")
    check("Adapter Validate", adapter_result.ok is True)

    print("PASS")


if __name__ == "__main__":
    main()
