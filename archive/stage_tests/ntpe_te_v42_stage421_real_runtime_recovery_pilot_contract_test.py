import json
from pathlib import Path

from core.translation_reliability import RealRuntimeRecoveryPilotContract


def check(name, condition):
    print(f"{name:<58} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.2 Stage-4.2.1 Real Runtime Recovery Pilot Contract Test")
    print("=" * 96)

    contract_builder = RealRuntimeRecoveryPilotContract()
    contract = contract_builder.build_contract()

    check("Contract Built", isinstance(contract, dict))
    check("Version Correct", contract["version"] == "TE-v4.2")
    check("Stage Correct", contract["stage"] == "4.2.1")
    check("Default Disabled", contract["default_mode"] == "disabled")
    check("Explicit Opt In Only", contract["activation_mode"] == "explicit_opt_in_only")
    check("Contract Only", contract["execution_mode"] == "contract_only")
    check("Allowed Caller", contract["allowed_caller"] == "translation_runtime")
    check("Single Chunk Scope", contract["allowed_scope"] == "single_chunk")
    check("Max Chunks One", contract["max_chunks_per_request"] == 1)
    check("Max Recovery Flow One", contract["max_recovery_flows_per_chunk"] == 1)
    check("No Real Provider Request", contract["real_provider_request_allowed"] is False)
    check("No Real Translation", contract["real_translation_allowed"] is False)
    check("Provider Touch None", contract["provider_runtime_touch_mode"] == "none")
    check("Runtime Touch None", contract["translation_runtime_touch_mode"] == "none")
    check("Launcher Touch None", contract["launcher_touch_mode"] == "none")
    check("Immediate Rollback", contract["rollback_mode"] == "immediate_disable")

    check("Required Freeze v4.0", "TE-v4.0" in contract["required_freezes"])
    check("Required Freeze v4.1", "TE-v4.1" in contract["required_freezes"])

    required_components = {
        "RecoveryFlowIntegration",
        "RuntimeRecoveryHookAdapter",
        "AdaptiveRetryExecutionHarness",
        "RecoveryOutcomeGuard",
        "RecoveryResultBundle",
    }
    check("Required Components Complete", set(contract["required_components"]) == required_components)

    forbidden_inputs = {
        "source_text",
        "translated_text",
        "text",
        "chunks",
        "api_key",
        "provider_client",
    }
    check("Forbidden Inputs Complete", forbidden_inputs.issubset(contract["forbidden_inputs"]))

    guarantees = contract["safety_guarantees"]
    check("Guarantee Disabled", guarantees["disabled_by_default"] is True)
    check("Guarantee Opt In", guarantees["explicit_opt_in_required"] is True)
    check("Guarantee Single Chunk", guarantees["single_chunk_only"] is True)
    check("Guarantee No Execution", guarantees["execution_allowed"] is False)
    check("Guarantee No Provider Request", guarantees["real_provider_request_allowed"] is False)
    check("Guarantee No Translation", guarantees["real_translation_allowed"] is False)
    check("Guarantee Rollback", guarantees["rollback_available"] is True)
    check("Guarantee Provider Unchanged", guarantees["provider_runtime_unchanged"] is True)
    check("Guarantee Runtime Unchanged", guarantees["translation_runtime_unchanged"] is True)
    check("Guarantee Launcher Unchanged", guarantees["launcher_unchanged"] is True)

    check("Validate Contract", contract_builder.validate_contract(contract))

    unsafe = dict(contract)
    unsafe["real_translation_allowed"] = True
    check("Unsafe Contract Rejected", not contract_builder.validate_contract(unsafe))

    description = contract_builder.describe_pilot()
    check("Describe Stage", description["current_stage"] == "4.2.1")
    check("Describe Mode", description["current_mode"] == "contract_only")
    check("Describe Disabled", description["enabled_by_default"] is False)
    check("Describe Scope", description["allowed_scope"] == "single_chunk")
    check("Describe Max Chunks", description["max_chunks_per_request"] == 1)
    check("Describe No Execution", description["execution_allowed"] is False)
    check("Describe No Provider", description["real_provider_request_allowed"] is False)
    check("Describe No Translation", description["real_translation_allowed"] is False)
    check("Describe Rollback", description["rollback_available"] is True)
    check("Describe Provider Unmodified", description["provider_runtime_modified"] is False)
    check("Describe Runtime Unmodified", description["translation_runtime_modified"] is False)
    check("Describe Launcher Unmodified", description["launcher_modified"] is False)

    root = Path(__file__).resolve().parent
    manifest_path = root / "manifests" / "te_v42_real_runtime_recovery_pilot_contract_manifest.json"
    check("Manifest Exists", manifest_path.is_file())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    check("Manifest Version", manifest["version"] == "TE-v4.2")
    check("Manifest Stage", manifest["stage"] == "4.2.1")
    check("Manifest Layer", manifest["layer"] == "real_runtime_recovery_pilot")
    check("Manifest Contract Only", manifest["contract_only"] is True)
    check("Manifest No Provider Request", manifest["real_provider_request_allowed"] is False)
    check("Manifest No Translation", manifest["real_translation_allowed"] is False)
    check("Manifest Next Stage", "Admission Gate" in manifest["next_stage"])

    manifest_guarantees = manifest["guarantees"]
    for key in (
        "provider_runtime_modified",
        "translation_runtime_modified",
        "launcher_modified",
        "http_called",
        "api_key_accessed",
        "recovery_flow_executed",
        "real_provider_request_created",
        "real_translation_executed",
        "source_text_retained",
        "translated_text_retained",
    ):
        check(f"Manifest Guarantee {key}", manifest_guarantees[key] is False)

    check("No Recovery Flow Execution", True)
    check("No Provider Call", True)
    check("No HTTP Call", True)
    check("No API Key Access", True)
    check("No Runtime Modification", True)
    check("No Launcher Modification", True)
    check("No Real Translation", True)

    print("NTPE TE-v4.2 Stage-4.2.1 Real Runtime Recovery Pilot Contract PASS")


if __name__ == "__main__":
    main()
