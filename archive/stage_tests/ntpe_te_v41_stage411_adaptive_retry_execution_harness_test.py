
from core.translation_reliability import AdaptiveRetryExecutionHarness


def check(name, condition):
    print(f"{name:<48} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.1 Stage-4.1.1 Adaptive Retry Execution Harness Test")
    print("=" * 84)

    harness = AdaptiveRetryExecutionHarness()

    disabled = harness.execute("abc", lambda text, ctx: {"outcome": "success", "translated_text": "ok"})
    check("Default Disabled", disabled["status"] == "disabled")
    check("Disabled Valid", harness.validate_result(disabled))

    call_state = {"count": 0}
    def timeout_then_success(text, context):
        call_state["count"] += 1
        if call_state["count"] == 1:
            return {
                "outcome": "read_timeout",
                "translated_text": "",
                "provider_attempts": 1,
                "latency_ms": 180000,
            }
        return {
            "outcome": "success",
            "translated_text": "完成",
            "provider_attempts": 1,
            "latency_ms": 50000,
        }

    timeout_result = harness.execute(
        "가" * 600,
        timeout_then_success,
        {
            "enabled": True,
            "max_attempts": 3,
            "chunk_size": 600,
            "min_chunk_size": 200,
            "timeout_seconds": 180,
        },
    )

    check("Timeout Recovery Completed", timeout_result["status"] == "completed")
    check("Timeout Recovery Success", timeout_result["success"] is True)
    check("Retry Executed", timeout_result["attempts_used"] == 2)
    check("Split Executed", timeout_result["split_count"] == 1)
    check("Result Valid", harness.validate_result(timeout_result))

    rebuild_state = {"calls": 0, "handler": 0}
    def rebuild():
        rebuild_state["calls"] += 1

    def provider_zero_then_success(text, context):
        rebuild_state["handler"] += 1
        if rebuild_state["handler"] == 1:
            return {
                "outcome": "provider_not_attempted",
                "translated_text": "",
                "provider_attempts": 0,
            }
        return {
            "outcome": "success",
            "translated_text": "完成",
            "provider_attempts": 1,
        }

    rebuild_result = harness.execute(
        "가" * 300,
        provider_zero_then_success,
        {"enabled": True, "max_attempts": 3, "chunk_size": 300},
        rebuild_callback=rebuild,
    )

    check("Rebuild Recovery Completed", rebuild_result["status"] == "completed")
    check("Rebuild Callback Called", rebuild_state["calls"] == 1)
    check("Rebuild Counted", rebuild_result["rebuild_count"] == 1)
    check("Rebuild Result Valid", harness.validate_result(rebuild_result))

    def auth_failure(text, context):
        return {
            "outcome": "authentication_error",
            "translated_text": "",
            "provider_attempts": 1,
        }

    auth_result = harness.execute(
        "가" * 100,
        auth_failure,
        {"enabled": True, "max_attempts": 3},
    )
    check("Authentication Stops", auth_result["status"] == "failed")
    check("Authentication No Retry", auth_result["attempts_used"] == 1)

    check("No Provider Runtime Modification", timeout_result["integration_status"]["provider_runtime_modified"] is False)
    check("No Translation Runtime Modification", timeout_result["integration_status"]["translation_runtime_modified"] is False)
    check("No Launcher Modification", timeout_result["integration_status"]["launcher_modified"] is False)
    check("No API Key Access", timeout_result["integration_status"]["api_key_accessed"] is False)
    check("No Real Runtime Used", timeout_result["integration_status"]["real_translation_runtime_used"] is False)
    check("Source Text Not Retained", timeout_result["source_text_retained"] is False)
    check("Translated Text Not Retained", timeout_result["translated_text_retained"] is False)

    print("NTPE TE-v4.1 Stage-4.1.1 Adaptive Retry Execution Harness PASS")


if __name__ == "__main__":
    main()
