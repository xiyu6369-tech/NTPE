import json
from pathlib import Path

from core.translation_reliability import (
    RealRuntimeRecoveryPilotDryRunBundle,
    RealRuntimeRecoveryPilotRollbackController,
)


def check(name, condition):
    print(f"{name:<68} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def admitted():
    return {
        "admitted": True,
        "status": "admitted_for_single_chunk_dry_run",
        "reason": "all_admission_checks_passed",
        "failed_checks": [],
    }


def rejected():
    return {
        "admitted": False,
        "status": "rejected",
        "reason": "feature_flag_disabled",
        "failed_checks": ["feature_flag_disabled"],
    }


def dry_success():
    return {
        "status": "dry_run_completed",
        "completed": True,
        "success": True,
        "handler_called": True,
        "result_summary": {
            "outcome": "success",
            "source_chars": 600,
            "translated_chars": 580,
            "provider_attempts": 1,
            "latency_ms": 50000,
        },
    }


def dry_failed():
    data = dry_success()
    data["status"] = "dry_run_failed"
    data["success"] = False
    data["result_summary"]["outcome"] = "empty_output"
    return data


def main():
    print("NTPE TE-v4.2 Stage-4.2.5 Real Runtime Recovery Pilot Dry-Run Bundle Test")
    print("=" * 108)

    bundler = RealRuntimeRecoveryPilotDryRunBundle()

    success = bundler.build("runtime-425", admitted(), dry_success(), metadata={"profile": "safe"})
    check("Success Bundle Status", success["status"] == "pilot_dry_run_succeeded")
    check("Success Bundle Successful", success["successful"] is True)
    check("Admission Summary", success["admission_summary"]["admitted"] is True)
    check("Dry Summary", success["dry_run_summary"]["success"] is True)
    check("Execution Disabled", success["execution_allowed"] is False)
    check("Provider Disabled", success["real_provider_request_allowed"] is False)
    check("Translation Disabled", success["real_translation_allowed"] is False)
    check("Success Is Successful", bundler.is_successful(success))
    check("Success Valid", bundler.validate_bundle(success))

    admission_rejected = bundler.build("runtime-425", rejected(), dry_success())
    check("Admission Rejected Status", admission_rejected["status"] == "pilot_admission_rejected")
    check("Admission Rejected Unsuccessful", admission_rejected["successful"] is False)
    check("Admission Rejected Valid", bundler.validate_bundle(admission_rejected))

    blocked_dry = dict(dry_failed())
    blocked_dry["status"] = "dry_run_blocked"
    blocked = bundler.build("runtime-425", admitted(), blocked_dry)
    check("Dry Blocked Status", blocked["status"] == "pilot_dry_run_blocked")
    check("Dry Blocked Valid", bundler.validate_bundle(blocked))

    failed = bundler.build("runtime-425", admitted(), dry_failed())
    check("Dry Failed Status", failed["status"] == "pilot_dry_run_failed")
    check("Dry Failed Valid", bundler.validate_bundle(failed))

    rollback = RealRuntimeRecoveryPilotRollbackController().request_rollback({"mode": "dry_run_completed"})
    rolled = bundler.build("runtime-425", admitted(), dry_success(), rollback)
    check("Rollback Status", rolled["status"] == "pilot_rolled_back")
    check("Rollback Summary", rolled["rollback_summary"]["rolled_back"] is True)
    check("Rollback Valid", bundler.validate_bundle(rolled))

    missing = bundler.build("runtime-425", admitted(), None)
    check("Missing Result Invalid Status", missing["status"] == "pilot_bundle_invalid")
    check("Missing Result Valid Shape", bundler.validate_bundle(missing))

    sanitized = bundler.build(
        "runtime-425",
        admitted(),
        dry_success(),
        metadata={
            "source_text": "raw source",
            "nested": [{"translated_text": "raw translated"}, {"api_key": "secret"}],
        },
    )
    payload = str(sanitized)
    check("Metadata Source Removed", "raw source" not in payload)
    check("Metadata Translated Removed", "raw translated" not in payload)
    check("Metadata Secret Removed", "secret" not in payload)
    check("Sanitized Valid", bundler.validate_bundle(sanitized))

    invalid = dict(success)
    invalid["execution_allowed"] = True
    check("Invalid Bundle Rejected", bundler.validate_bundle(invalid) is False)

    root = Path(__file__).resolve().parent
    manifest_path = root / "manifests" / "te_v42_real_runtime_recovery_pilot_dry_run_bundle_manifest.json"
    check("Manifest Exists", manifest_path.is_file())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    check("Manifest Version", manifest["version"] == "TE-v4.2")
    check("Manifest Stage", manifest["stage"] == "4.2.5")
    check("Manifest Layer", manifest["layer"] == "real_runtime_recovery_pilot_dry_run_bundle")
    check("Manifest Safe Summary", manifest["safe_summary_only"] is True)
    for key, expected in manifest["guarantees"].items():
        check(f"Manifest Guarantee {key}", expected is False)

    print("NTPE TE-v4.2 Stage-4.2.5 Real Runtime Recovery Pilot Dry-Run Bundle PASS")


if __name__ == "__main__":
    main()
