from core.translation_reliability import TranslationRuntimeRecoveryHookContract


def check(name, condition):
    print(f"{name:<58} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.3 Stage-4.3.1 Runtime Recovery Hook Contract Test")
    print("=" * 86)
    builder = TranslationRuntimeRecoveryHookContract()
    contract = builder.build_contract()
    desc = builder.describe_hook()

    check("Contract Built", contract["version"] == "TE-v4.3")
    check("Default Disabled", contract["default_mode"] == "disabled")
    check("Explicit Opt In", contract["activation_mode"] == "explicit_opt_in_only")
    check("Shadow Only", contract["execution_mode"] == "shadow_only")
    check("Single Chunk", contract["allowed_scope"] == "single_chunk")
    check("No Result Replacement", contract["result_replacement_allowed"] is False)
    check("No Provider Fallback", contract["provider_fallback_allowed"] is False)
    check("No Real Provider Request", contract["real_provider_request_allowed"] is False)
    check("Rollback Immediate", contract["rollback_mode"] == "immediate_disable")
    check("Required Freezes", set(contract["required_freezes"]) == {"TE-v4.0", "TE-v4.1", "TE-v4.2"})
    check("Required Components", "RealRuntimeRecoveryPilotDryRunBundle" in contract["required_components"])
    check("Contract Valid", builder.validate_contract(contract))
    check("Describe Hook", desc["current_mode"] == "shadow_only")
    check("Runtime Main Flow Unchanged", desc["translation_runtime_main_flow_modified"] is False)
    check("Provider Unchanged", desc["provider_runtime_modified"] is False)
    check("Launcher Unchanged", desc["launcher_modified"] is False)
    print("NTPE TE-v4.3 Stage-4.3.1 Runtime Recovery Hook Contract PASS")


if __name__ == "__main__":
    main()
