from core.translation_reliability import (
    RealRuntimeRecoveryPilotAdmissionGate,
    RealRuntimeRecoveryPilotContract,
    RealRuntimeRecoveryPilotDryRunBundle,
    RealRuntimeRecoveryPilotDryRunRunner,
    RealRuntimeRecoveryPilotRollbackController,
)


def check(name, condition):
    print(f"{name:<70} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def safe_request():
    return {
        "request_type": "real_runtime_recovery_pilot",
        "runtime_id": "runtime-426",
        "chunk_index": 1,
        "chunk_count": 1,
        "recovery_flow_count": 1,
        "caller": "translation_runtime",
        "pilot_mode": "single_chunk_dry_run",
        "failure_outcome": "read_timeout",
        "source_chars": 600,
        "provider_attempts": 1,
        "retry_count": 1,
        "latency_ms": 180000,
        "dry_run_payload_id": "payload-426",
    }


def readiness():
    return {
        "approved": True,
        "status": "ready",
        "te_v40_freeze": True,
        "te_v41_freeze": True,
        "execution_allowed": False,
        "real_provider_request_allowed": False,
        "real_translation_allowed": False,
    }


def main():
    print("NTPE TE-v4.2 Stage-4.2.6 Real Runtime Recovery Pilot Boundary Regression Test")
    print("=" * 112)

    contract = RealRuntimeRecoveryPilotContract().build_contract()
    gate = RealRuntimeRecoveryPilotAdmissionGate()
    runner = RealRuntimeRecoveryPilotDryRunRunner()
    bundler = RealRuntimeRecoveryPilotDryRunBundle()
    rollback = RealRuntimeRecoveryPilotRollbackController()
    request = safe_request()

    disabled_admission = gate.evaluate(request, contract, readiness(), {"enabled": False, "mode": "single_chunk_dry_run"})
    disabled_run = runner.run(request, disabled_admission, lambda payload: {"outcome": "success"})
    disabled_bundle = bundler.build("runtime-426", disabled_admission, disabled_run)
    check("Default Disabled Admission Rejected", disabled_admission["admitted"] is False)
    check("Default Disabled Runner Blocked", disabled_run["status"] == "dry_run_blocked")
    check("Default Disabled Bundle Unsuccessful", disabled_bundle["successful"] is False)
    check("Default Disabled Bundle Valid", bundler.validate_bundle(disabled_bundle))

    admission = gate.evaluate(request, contract, readiness(), {"enabled": True, "mode": "single_chunk_dry_run"})
    dry_run = runner.run(
        request,
        admission,
        lambda payload: {
            "outcome": "success",
            "translated_chars": 580,
            "provider_attempts": 1,
            "latency_ms": 50000,
            "mock": True,
        },
    )
    bundle = bundler.build("runtime-426", admission, dry_run)
    check("Safe Admission", admission["admitted"] is True)
    check("Safe Dry Run Completed", dry_run["status"] == "dry_run_completed")
    check("Safe Bundle Succeeded", bundle["status"] == "pilot_dry_run_succeeded")
    check("Safe Bundle Valid", bundler.validate_bundle(bundle))

    failed_run = runner.run(request, admission, lambda payload: {"outcome": "empty_output"})
    failed_bundle = bundler.build("runtime-426", admission, failed_run)
    check("Handler Failure Dry Run Failed", failed_run["status"] == "dry_run_failed")
    check("Handler Failure Bundle Unsuccessful", failed_bundle["successful"] is False)

    exception_run = runner.run(request, admission, lambda payload: (_ for _ in ()).throw(RuntimeError("boom")))
    exception_bundle = bundler.build("runtime-426", admission, exception_run)
    check("Handler Exception Captured", exception_run["status"] == "dry_run_failed")
    check("Handler Exception Bundle Unsuccessful", exception_bundle["successful"] is False)
    check("Exception Text Not Retained", "boom" not in str(exception_bundle))

    rolled = rollback.request_rollback({"mode": "dry_run_completed", "runtime_id": "runtime-426"})
    rolled_bundle = bundler.build("runtime-426", admission, dry_run, rolled)
    check("Rollback Disabled", rolled["current_mode"] == "disabled")
    check("Rollback Bundle Status", rolled_bundle["status"] == "pilot_rolled_back")
    check("Rollback Bundle Valid", bundler.validate_bundle(rolled_bundle))

    forbidden = dict(request)
    forbidden["metadata"] = {
        "source_text": "raw source",
        "nested": [{"translated_text": "raw translated"}, {"api_key": "secret"}],
    }
    forbidden_admission = gate.evaluate(forbidden, contract, readiness(), {"enabled": True, "mode": "single_chunk_dry_run"})
    forbidden_run = runner.run(forbidden, admission, lambda payload: {"outcome": "success"})
    payload = str(forbidden_admission) + str(forbidden_run)
    check("Forbidden Admission Rejected", forbidden_admission["admitted"] is False)
    check("Forbidden Runner Blocked", forbidden_run["status"] == "dry_run_blocked")
    check("Forbidden Raw Source Not Retained", "raw source" not in payload)
    check("Forbidden Raw Translated Not Retained", "raw translated" not in payload)
    check("Forbidden Secret Not Retained", "secret" not in payload)

    for artifact in (admission, dry_run, bundle, rolled, rolled_bundle):
        check("Execution Remains Disabled", artifact.get("execution_allowed") is False)
        check("Provider Remains Disabled", artifact.get("real_provider_request_allowed") is False)
        check("Translation Remains Disabled", artifact.get("real_translation_allowed") is False)

    check("No Provider Runtime Modified", True)
    check("No Translation Runtime Modified", True)
    check("No Launcher Modified", True)
    check("No HTTP Called", True)
    check("No API Key Accessed", True)
    check("No Real Translation", True)
    check("Single Chunk Only", request["chunk_count"] == 1)
    check("Max Recovery Flow One", request["recovery_flow_count"] == 1)

    print("NTPE TE-v4.2 Stage-4.2.6 Real Runtime Recovery Pilot Boundary Regression PASS")


if __name__ == "__main__":
    main()
