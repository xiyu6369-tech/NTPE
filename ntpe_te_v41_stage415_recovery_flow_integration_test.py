
from core.translation_reliability import RecoveryFlowIntegration


def check(name, condition):
    print(f"{name:<52} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.1 Stage-4.1.5 Recovery Flow Integration Test")
    print("=" * 86)

    flow = RecoveryFlowIntegration()

    blocked = flow.run(
        {
            "runtime_id": "demo-415",
            "caller": "translation_runtime",
            "source_text": "가" * 100,
        },
        handler=lambda text, context: {
            "outcome": "success",
            "translated_text": "譯" * 90,
        },
    )
    check("Default Disabled Flow Blocked", blocked["status"] == "flow_blocked")
    check("Blocked Result Valid", flow.validate_result(blocked))

    timeout_state = {"calls": 0}
    def timeout_then_success(text, context):
        timeout_state["calls"] += 1
        if timeout_state["calls"] == 1:
            return {
                "outcome": "read_timeout",
                "translated_text": "",
                "provider_attempts": 1,
            }
        return {
            "outcome": "success",
            "translated_text": "譯" * max(1, int(len(text) * 0.9)),
            "provider_attempts": 1,
        }

    timeout_result = flow.run(
        {
            "enabled": True,
            "runtime_id": "demo-timeout",
            "caller": "translation_runtime",
            "source_text": "가" * 600,
            "max_attempts": 3,
            "chunk_size": 600,
            "min_chunk_size": 200,
            "min_length_ratio": 0.35,
        },
        handler=timeout_then_success,
    )
    check("Timeout Flow Completed", timeout_result["status"] == "flow_completed")
    check("Timeout Flow Accepted", timeout_result["accepted"] is True)
    check("Timeout Split Counted", timeout_result["bundle"]["recovery_summary"]["split_count"] == 1)
    check("Timeout Result Valid", flow.validate_result(timeout_result))

    rebuild_state = {"handler": 0, "rebuild": 0}
    def rebuild():
        rebuild_state["rebuild"] += 1

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
            "translated_text": "譯" * max(1, int(len(text) * 0.9)),
            "provider_attempts": 1,
        }

    provider_result = flow.run(
        {
            "enabled": True,
            "runtime_id": "demo-provider-zero",
            "caller": "translation_runtime",
            "source_text": "가" * 300,
            "max_attempts": 3,
            "chunk_size": 300,
        },
        handler=provider_zero_then_success,
        rebuild_callback=rebuild,
    )
    check("Provider Zero Flow Completed", provider_result["status"] == "flow_completed")
    check("Provider Rebuild Executed", rebuild_state["rebuild"] == 1)
    check("Provider Rebuild Counted", provider_result["bundle"]["recovery_summary"]["rebuild_count"] == 1)
    check("Provider Result Valid", flow.validate_result(provider_result))

    def too_short(text, context):
        return {
            "outcome": "success",
            "translated_text": "短",
            "provider_attempts": 1,
        }

    short_result = flow.run(
        {
            "enabled": True,
            "runtime_id": "demo-short",
            "caller": "translation_runtime",
            "source_text": "가" * 100,
            "max_attempts": 1,
            "chunk_size": 100,
            "min_length_ratio": 0.35,
        },
        handler=too_short,
    )
    check("Too Short Flow Rejected", short_result["status"] == "flow_rejected")
    check("Too Short Not Accepted", short_result["accepted"] is False)
    check("Too Short Issue Preserved", "too_short" in short_result["bundle"]["guard_summary"]["issues"])
    check("Too Short Result Valid", flow.validate_result(short_result))

    def auth_error(text, context):
        return {
            "outcome": "authentication_error",
            "translated_text": "",
            "provider_attempts": 1,
        }

    auth_result = flow.run(
        {
            "enabled": True,
            "runtime_id": "demo-auth",
            "caller": "translation_runtime",
            "source_text": "가" * 100,
            "max_attempts": 3,
        },
        handler=auth_error,
    )
    check("Auth Flow Rejected", auth_result["status"] == "flow_rejected")
    check("Auth Hook Failed", auth_result["hook_result"]["status"] == "recovery_failed")
    check("Auth Result Valid", flow.validate_result(auth_result))

    payload = str(timeout_result)
    check("Source Text Not Retained", "가" * 20 not in payload)
    check("Translated Text Not Retained", "譯" * 20 not in payload)
    check("No Runtime Modification", timeout_result["integration_status"]["translation_runtime_modified"] is False)
    check("No Provider Modification", timeout_result["integration_status"]["provider_runtime_modified"] is False)
    check("No HTTP Call", timeout_result["integration_status"]["http_called"] is False)
    check("No API Key Access", timeout_result["integration_status"]["api_key_accessed"] is False)
    check("No Real Runtime", timeout_result["integration_status"]["real_translation_runtime_used"] is False)

    print("NTPE TE-v4.1 Stage-4.1.5 Recovery Flow Integration PASS")


if __name__ == "__main__":
    main()
