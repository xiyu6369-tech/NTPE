import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.pipeline.recovery_executor import (
    RecoveryExecutionResult,
    RecoveryExecutorAdapter,
    normalize_execution_result,
    validate_execution_result,
    create_error_record,
    append_executor_event,
    prepare_execution_state,
    execute_with_recovery,
)


def check(name, cond):
    print(f"{name:<24} {'PASS' if cond else 'FAIL'}")
    if not cond:
        raise AssertionError(name)


def main():
    print("NTPE Foundation-04.9 Pipeline Recovery Executor Test")
    print("=" * 56)

    nr = normalize_execution_result(RecoveryExecutionResult(status="completed", output="ok", attempts=1))
    check("Result Created", nr["status"] == "completed")
    check("Validate Result", validate_execution_result(nr))

    try:
        raise TimeoutError("timeout while translating")
    except Exception as exc:
        er = create_error_record(exc, attempt=2)
    check("Error Record", er["category"] == "timeout")
    check("Error Attempt", er["attempt"] == 2)

    trace = append_executor_event({"events": []}, "unit_event", value=1)
    check("Trace Event", trace["events"][-1]["type"] == "unit_event")

    st = prepare_execution_state({}, {"max_attempts": 2, "base_delay_seconds": 0})
    check("State Prepared", st["status"] == "ready")
    check("Policy Attached", "retry_policy" in st)

    ok = execute_with_recovery(lambda payload, state: payload["source"] + "_done", {"source": "x"}, policy={"max_attempts": 2})
    check("Execute Success", ok["status"] == "completed")
    check("Success Output", ok["output"] == "x_done")
    check("Success Trace", ok["trace"]["events"])

    calls = {"n": 0}
    def flaky(payload, state):
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("timeout")
        return "recovered"

    retry = execute_with_recovery(flaky, {}, policy={"max_attempts": 3, "base_delay_seconds": 0})
    check("Execute Retry", retry["status"] == "completed")
    check("Retry Attempts", retry["attempts"] == 2)
    check("Retry Decision", retry["decisions"][0]["action"] == "retry")

    def bad_quality(payload, state):
        raise RuntimeError("quality failed")

    fallback = execute_with_recovery(
        bad_quality,
        {},
        policy={"max_attempts": 5, "fallback_after": 1, "base_delay_seconds": 0},
        fallback=lambda payload, state: "fallback_output",
    )
    check("Execute Fallback", fallback["status"] == "fallback_completed")
    check("Fallback Output", fallback["output"] == "fallback_output")
    check("Fallback Used", fallback["used_fallback"] is True)

    fallback_fail = execute_with_recovery(
        bad_quality,
        {},
        policy={"max_attempts": 5, "fallback_after": 1, "base_delay_seconds": 0},
        fallback=lambda payload, state: (_ for _ in ()).throw(RuntimeError("fallback broke")),
    )
    check("Fallback Failed", fallback_fail["status"] == "fallback_failed")

    abort = execute_with_recovery(lambda payload, state: (_ for _ in ()).throw(RuntimeError("fatal error")), {}, policy={"max_attempts": 3})
    check("Execute Abort", abort["status"] == "aborted")
    check("Abort Error", abort["last_error"]["category"] == "fatal")

    adapter = RecoveryExecutorAdapter(policy={"max_attempts": 2, "base_delay_seconds": 0}, fallback=lambda p, s: "fb")
    payload = adapter.before({"source": "x"}, {})
    check("Adapter Before", "retry_policy" in payload)

    ast = {}
    result = adapter.execute(lambda payload, state: "adapter_ok", payload, ast)
    check("Adapter Execute", result["status"] == "completed")
    adapter.after(payload, ast)
    check("Adapter After", ast["trace"]["events"])

    print("PASS")


if __name__ == "__main__":
    main()
