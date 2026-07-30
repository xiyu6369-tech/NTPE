
from core.translation_reliability import RuntimeRecoveryHookAdapter


def check(name, condition):
    print(f"{name:<50} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.1 Stage-4.1.2 Runtime Recovery Hook Adapter Test")
    print("=" * 84)

    adapter = RuntimeRecoveryHookAdapter()

    blocked = adapter.invoke(
        {
            "runtime_id": "demo-412",
            "caller": "translation_runtime",
            "source_text": "가" * 100,
        },
        handler=lambda text, context: {
            "outcome": "success",
            "translated_text": "完成",
        },
    )
    check("Default Disabled", blocked["status"] == "blocked")
    check("Disabled Reason", blocked["reason"] == "hook_disabled")
    check("Disabled Valid", adapter.validate_result(blocked))

    wrong_caller = adapter.invoke(
        {
            "enabled": True,
            "runtime_id": "demo-412",
            "caller": "launcher",
            "source_text": "가" * 100,
        },
        handler=lambda text, context: {
            "outcome": "success",
            "translated_text": "完成",
        },
    )
    check("Wrong Caller Blocked", wrong_caller["reason"] == "invalid_caller")

    state = {"calls": 0}
    def timeout_then_success(text, context):
        state["calls"] += 1
        if state["calls"] == 1:
            return {
                "outcome": "read_timeout",
                "translated_text": "",
                "provider_attempts": 1,
            }
        return {
            "outcome": "success",
            "translated_text": "完成",
            "provider_attempts": 1,
        }

    result = adapter.invoke(
        {
            "enabled": True,
            "runtime_id": "demo-412",
            "caller": "translation_runtime",
            "source_text": "가" * 600,
            "max_attempts": 3,
            "chunk_size": 600,
            "min_chunk_size": 200,
        },
        handler=timeout_then_success,
    )

    check("Recovery Completed", result["status"] == "recovery_completed")
    check("Allowed", result["allowed"] is True)
    check("Not Blocked", result["blocked"] is False)
    check("Runtime ID Preserved", result["runtime_id"] == "demo-412")
    check("Attempts Counted", result["recovery_summary"]["attempts_used"] == 2)
    check("Split Counted", result["recovery_summary"]["split_count"] == 1)
    check("Final Outcome Success", result["recovery_summary"]["final_outcome"] == "success")
    check("Result Valid", adapter.validate_result(result))

    payload = str(result)
    check("Source Text Not Retained", "가" * 20 not in payload)
    check("Translated Text Not Retained", "完成" not in payload)
    check("Runtime Hook Invoked", result["integration_status"]["runtime_hook_invoked"] is True)
    check("Runtime Not Modified", result["integration_status"]["runtime_modified"] is False)
    check("Provider Not Modified", result["integration_status"]["provider_runtime_modified"] is False)
    check("Launcher Not Modified", result["integration_status"]["launcher_modified"] is False)
    check("No API Key Access", result["integration_status"]["api_key_accessed"] is False)
    check("No Real Runtime", result["integration_status"]["real_translation_runtime_used"] is False)

    print("NTPE TE-v4.1 Stage-4.1.2 Runtime Recovery Hook Adapter PASS")


if __name__ == "__main__":
    main()
