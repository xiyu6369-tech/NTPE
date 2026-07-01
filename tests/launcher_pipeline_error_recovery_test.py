r"""
NTPE Foundation-04.7 Pipeline Error Recovery Contract Test
Run:
    python tests\launcher_pipeline_error_recovery_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.pipeline_error_recovery_adapter import PipelineErrorRecoveryAdapter
from core.pipeline_error_recovery_contract import (
    apply_recovery,
    attach_recovery_to_state,
    classify_recovery_action,
    create_recovery_record,
    mark_recovery_applied,
    normalize_recovery_record,
    plan_recovery,
    recover_call,
    validate_recovery_record,
)
from core.pipeline_execution_trace import create_execution_trace
from core.pipeline_state_contract import create_pipeline_state


def check(label: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"{label:<24} {status}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    print("NTPE Foundation-04.7 Pipeline Error Recovery Contract Test")
    print("=" * 68)

    payload = {"text": "안녕하세요.", "language": "繁體中文"}
    state = create_pipeline_state(payload, stage="quality")
    state["execution_trace"] = create_execution_trace(trace_id="recovery-trace")

    record = create_recovery_record(stage="quality", error="timeout", action="retry", attempt=0, max_attempts=2)
    check("Record Created", record["recovery_version"] == "04.7")
    check("Record Action", record["action"] == "retry")

    legacy = normalize_recovery_record({"decision": "fallback", "retry_count": 3, "stage": "prompt", "error": {"message": "503"}})
    check("Legacy Normalize", legacy["action"] == "fallback")
    check("Legacy Attempt", legacy["attempt"] == 3)

    validated = validate_recovery_record(record)
    check("Validate Record", validated.ok is True)
    check("Validate Status", validated.status == "pending")

    check("Classify Retry", classify_recovery_action("timeout", attempt=0, max_attempts=2) == "retry")
    check("Classify Fallback", classify_recovery_action("timeout", attempt=2, max_attempts=2, fallback_available=True) == "fallback")
    check("Classify Abort", classify_recovery_action("invalid payload", attempt=0, max_attempts=2) == "abort")

    attached = attach_recovery_to_state(state, record)
    check("Attach Recovery", attached["recovery"]["current"]["action"] == "retry")
    check("Attach History", attached["recovery"]["summary"]["recovery_count"] == 1)
    check("Attach Trace", attached["execution_trace"]["events"][-1]["name"].startswith("recovery:"))

    planned = plan_recovery(state, "quality", "timeout", attempt=0, max_attempts=2)
    check("Plan Recovery", planned.action == "retry")
    check("Plan State", planned.state["recovery"]["current"]["stage"] == "quality")

    applied = mark_recovery_applied(planned.state, planned.recovery)
    check("Mark Applied", applied["recovery"]["current"]["status"] == "applied")
    check("Applied Status", applied["status"] == "running")

    def retry_stage(current_state):
        current_state["retry_output"] = "ok"
        return current_state

    retry_result = apply_recovery(planned.state, planned.recovery, retry_fn=retry_stage)
    check("Apply Retry", retry_result.ok is True)
    check("Retry Output", retry_result.state["retry_output"] == "ok")

    fallback_record = create_recovery_record(stage="prompt", error="503", action="fallback", fallback_stage="prompt:fallback")

    def fallback_stage(current_state):
        current_state["fallback_output"] = "ok"
        return current_state

    fallback_result = apply_recovery(attach_recovery_to_state(state, fallback_record), fallback_record, fallback_fn=fallback_stage)
    check("Apply Fallback", fallback_result.ok is True)
    check("Fallback Output", fallback_result.state["fallback_output"] == "ok")

    abort_record = create_recovery_record(stage="context", error="invalid payload", action="abort")
    abort_result = apply_recovery(attach_recovery_to_state(state, abort_record), abort_record)
    check("Apply Abort", abort_result.ok is False)
    check("Abort Status", abort_result.state["status"] == "failed")

    calls = {"count": 0}

    def unstable_stage(current_state):
        calls["count"] += 1
        if calls["count"] < 2:
            raise RuntimeError("timeout")
        current_state["recovered"] = True
        return current_state

    recovered = recover_call(state, "narrative", unstable_stage, max_attempts=2)
    check("Recover Call", recovered.get("recovered") is True)
    check("Recover Attempts", calls["count"] == 2)

    def always_bad(current_state):
        raise RuntimeError("timeout")

    recovered_fallback = recover_call(state, "adapter", always_bad, fallback_fn=fallback_stage, max_attempts=1)
    check("Recover Fallback", recovered_fallback.get("fallback_output") == "ok")

    adapter = PipelineErrorRecoveryAdapter()
    adapter_plan = adapter.plan(state, "quality", "timeout", attempt=0, max_attempts=2)
    adapter_applied = adapter.apply(adapter_plan.state, adapter_plan.recovery, retry_fn=retry_stage)
    check("Adapter Plan", adapter_plan.action == "retry")
    check("Adapter Apply", adapter_applied.state["retry_output"] == "ok")
    check("Adapter Classify", adapter.classify("invalid status") == "abort")

    print("PASS")


if __name__ == "__main__":
    main()
