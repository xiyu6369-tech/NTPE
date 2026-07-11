
import json
from pathlib import Path

from core.translation_reliability import (
    AdaptiveRetryExecutionHarness,
    RuntimeRecoveryHookAdapter,
    RecoveryOutcomeGuard,
    RecoveryResultBundle,
    RecoveryFlowIntegration,
)


def check(name, condition):
    print(f"{name:<56} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.1 Stage-4.1.7 Translation Reliability Execution Freeze Test")
    print("=" * 94)

    root = Path(__file__).resolve().parent
    manifest_path = (
        root
        / "manifests"
        / "te_v41_translation_reliability_execution_freeze_manifest.json"
    )
    check("Freeze Manifest Exists", manifest_path.is_file())

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    check("Version Correct", manifest["version"] == "TE-v4.1")
    check("Stage Correct", manifest["stage"] == "4.1.7")
    check("Layer Correct", manifest["layer"] == "translation_reliability_execution")
    check("Freeze Enabled", manifest["frozen"] is True)
    check(
        "Stages Complete",
        manifest["stages"] == ["4.1.1", "4.1.2", "4.1.3", "4.1.4", "4.1.5", "4.1.6"],
    )

    expected_components = {
        "AdaptiveRetryExecutionHarness",
        "RuntimeRecoveryHookAdapter",
        "RecoveryOutcomeGuard",
        "RecoveryResultBundle",
        "RecoveryFlowIntegration",
        "RecoveryFlowBoundaryRegression",
    }
    check("Components Complete", set(manifest["components"]) == expected_components)

    guarantees = manifest["guarantees"]
    for key in (
        "provider_runtime_modified",
        "translation_runtime_modified",
        "launcher_modified",
        "http_called",
        "api_key_accessed",
        "real_translation_runtime_used",
        "source_text_retained",
        "translated_text_retained",
        "authentication_error_retried",
        "too_short_output_accepted",
    ):
        check(f"Guarantee {key}", guarantees[key] is False)

    check("Harness Import", AdaptiveRetryExecutionHarness is not None)
    check("Hook Import", RuntimeRecoveryHookAdapter is not None)
    check("Guard Import", RecoveryOutcomeGuard is not None)
    check("Bundle Import", RecoveryResultBundle is not None)
    check("Flow Import", RecoveryFlowIntegration is not None)

    flow = RecoveryFlowIntegration()

    blocked = flow.run(
        {
            "runtime_id": "freeze-disabled",
            "caller": "translation_runtime",
            "source_text": "가" * 100,
        },
        handler=lambda text, context: {
            "outcome": "success",
            "translated_text": "譯" * 90,
        },
    )
    check("Default Flow Blocked", blocked["status"] == "flow_blocked")
    check("Blocked Flow Valid", flow.validate_result(blocked))

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
            "translated_text": "譯" * max(1, int(len(text) * 0.9)),
            "provider_attempts": 1,
        }

    completed = flow.run(
        {
            "enabled": True,
            "runtime_id": "freeze-timeout",
            "caller": "translation_runtime",
            "source_text": "가" * 600,
            "max_attempts": 3,
            "chunk_size": 600,
            "min_chunk_size": 200,
        },
        handler=timeout_then_success,
    )
    check("Timeout Recovery Accepted", completed["status"] == "flow_completed")
    check("Timeout Flow Valid", flow.validate_result(completed))
    check(
        "Timeout Split Used",
        completed["bundle"]["recovery_summary"]["split_count"] == 1,
    )

    short = flow.run(
        {
            "enabled": True,
            "runtime_id": "freeze-short",
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
    check("Too Short Issue Present", "too_short" in short["guard_result"]["issues"])

    auth = flow.run(
        {
            "enabled": True,
            "runtime_id": "freeze-auth",
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
    check(
        "Authentication Single Attempt",
        auth["hook_result"]["recovery_summary"]["attempts_used"] == 1,
    )

    payload = str(completed)
    check("Source Text Not Retained", "가" * 20 not in payload)
    check("Translated Text Not Retained", "譯" * 20 not in payload)

    integration = completed["integration_status"]
    check("Provider Runtime Unchanged", integration["provider_runtime_modified"] is False)
    check("Translation Runtime Unchanged", integration["translation_runtime_modified"] is False)
    check("Launcher Unchanged", integration["launcher_modified"] is False)
    check("HTTP Not Called", integration["http_called"] is False)
    check("API Key Not Accessed", integration["api_key_accessed"] is False)
    check("Real Runtime Not Used", integration["real_translation_runtime_used"] is False)

    check(
        "Next Stage Defined",
        manifest["next_stage"] == "TE-v4.2 Real Runtime Recovery Pilot Planning",
    )

    print("NTPE TE-v4.1 Stage-4.1.7 Translation Reliability Execution Freeze PASS")


if __name__ == "__main__":
    main()
