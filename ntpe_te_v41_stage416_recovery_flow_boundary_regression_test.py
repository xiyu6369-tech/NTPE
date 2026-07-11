
from core.translation_reliability import RecoveryFlowIntegration


def check(name, condition):
    print(f"{name:<54} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.1 Stage-4.1.6 Recovery Flow Boundary Regression Test")
    print("=" * 90)

    flow = RecoveryFlowIntegration()

    blocked = flow.run(
        {
            "runtime_id": "boundary-disabled",
            "caller": "translation_runtime",
            "source_text": "가" * 100,
        },
        handler=lambda text, context: {
            "outcome": "success",
            "translated_text": "譯" * 90,
        },
    )
    check("Default Path Blocked", blocked["status"] == "flow_blocked")
    check("Blocked Path Not Accepted", blocked["accepted"] is False)
    check("Blocked Result Valid", flow.validate_result(blocked))

    timeout_state = {"calls": 0}
    def timeout_then_success(text, context):
        timeout_state["calls"] += 1
        if timeout_state["calls"] == 1:
            return {
                "outcome": "read_timeout",
                "translated_text": "",
                "provider_attempts": 1,
                "latency_ms": 180000,
            }
        return {
            "outcome": "success",
            "translated_text": "譯" * max(1, int(len(text) * 0.9)),
            "provider_attempts": 1,
            "latency_ms": 50000,
        }

    completed = flow.run(
        {
            "enabled": True,
            "runtime_id": "boundary-timeout",
            "caller": "translation_runtime",
            "source_text": "가" * 600,
            "max_attempts": 3,
            "chunk_size": 600,
            "min_chunk_size": 200,
            "api_key": "must-not-retain",
            "provider_client": "must-not-retain",
            "profile": "literary",
        },
        handler=timeout_then_success,
    )
    check("Recovery Flow Completed", completed["status"] == "flow_completed")
    check("Recovery Accepted", completed["accepted"] is True)
    check("Recovery Result Valid", flow.validate_result(completed))

    payload = str(completed)
    check("Source Text Not Retained", "가" * 20 not in payload)
    check("Translated Text Not Retained", "譯" * 20 not in payload)
    check("API Key Not Retained", "must-not-retain" not in payload)

    integration = completed["integration_status"]
    check("Provider Runtime Unchanged", integration["provider_runtime_modified"] is False)
    check("Translation Runtime Unchanged", integration["translation_runtime_modified"] is False)
    check("Launcher Unchanged", integration["launcher_modified"] is False)
    check("HTTP Not Called", integration["http_called"] is False)
    check("API Key Not Accessed", integration["api_key_accessed"] is False)
    check("Real Runtime Not Used", integration["real_translation_runtime_used"] is False)

    hook_integration = completed["hook_result"]["integration_status"]
    check("Hook Runtime Unchanged", hook_integration["runtime_modified"] is False)
    check("Hook Provider Unchanged", hook_integration["provider_runtime_modified"] is False)
    check("Hook Launcher Unchanged", hook_integration["launcher_modified"] is False)
    check("Hook HTTP Client Not Imported", hook_integration["http_client_imported"] is False)
    check("Hook API Key Not Accessed", hook_integration["api_key_accessed"] is False)
    check("Hook Real Runtime Not Used", hook_integration["real_translation_runtime_used"] is False)

    harness_integration = completed["hook_result"]["harness_result"]["integration_status"]
    check("Harness Provider Runtime Unchanged", harness_integration["provider_runtime_modified"] is False)
    check("Harness Translation Runtime Unchanged", harness_integration["translation_runtime_modified"] is False)
    check("Harness Launcher Unchanged", harness_integration["launcher_modified"] is False)
    check("Harness HTTP Client Not Imported", harness_integration["http_client_imported"] is False)
    check("Harness API Key Not Accessed", harness_integration["api_key_accessed"] is False)
    check("Harness Real Runtime Not Used", harness_integration["real_translation_runtime_used"] is False)

    guard_integration = completed["guard_result"]["integration_status"]
    check("Guard Provider Not Called", guard_integration["provider_called"] is False)
    check("Guard HTTP Not Called", guard_integration["http_called"] is False)
    check("Guard API Key Not Accessed", guard_integration["api_key_accessed"] is False)
    check("Guard Runtime Unchanged", guard_integration["runtime_modified"] is False)
    check("Guard Launcher Unchanged", guard_integration["launcher_modified"] is False)
    check("Guard Real Translation Not Executed", guard_integration["real_translation_executed"] is False)

    bundle_integration = completed["bundle"]["integration_status"]
    check("Bundle Runtime Unchanged", bundle_integration["runtime_modified"] is False)
    check("Bundle Provider Unchanged", bundle_integration["provider_runtime_modified"] is False)
    check("Bundle Launcher Unchanged", bundle_integration["launcher_modified"] is False)
    check("Bundle HTTP Not Called", bundle_integration["http_called"] is False)
    check("Bundle API Key Not Accessed", bundle_integration["api_key_accessed"] is False)
    check("Bundle Real Runtime Not Used", bundle_integration["real_translation_runtime_used"] is False)

    short = flow.run(
        {
            "enabled": True,
            "runtime_id": "boundary-short",
            "caller": "translation_runtime",
            "source_text": "가" * 100,
            "max_attempts": 1,
            "chunk_size": 100,
        },
        handler=lambda text, context: {
            "outcome": "success",
            "translated_text": "短",
            "provider_attempts": 1,
        },
    )
    check("Too Short Rejected", short["status"] == "flow_rejected")
    check("Too Short Boundary Valid", flow.validate_result(short))
    check("Too Short Issue Preserved", "too_short" in short["guard_result"]["issues"])

    auth = flow.run(
        {
            "enabled": True,
            "runtime_id": "boundary-auth",
            "caller": "translation_runtime",
            "source_text": "가" * 100,
            "max_attempts": 3,
        },
        handler=lambda text, context: {
            "outcome": "authentication_error",
            "translated_text": "",
            "provider_attempts": 1,
        },
    )
    check("Authentication Rejected", auth["status"] == "flow_rejected")
    check("Authentication No Retry", auth["hook_result"]["recovery_summary"]["attempts_used"] == 1)
    check("Authentication Boundary Valid", flow.validate_result(auth))

    print("NTPE TE-v4.1 Stage-4.1.6 Recovery Flow Boundary Regression PASS")


if __name__ == "__main__":
    main()
