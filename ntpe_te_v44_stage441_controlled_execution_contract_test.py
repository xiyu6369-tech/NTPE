from core.translation_reliability import ControlledExecutionContract


def check(name, condition):
    print(f"{name:<60} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.4 Stage-4.4.1 Controlled Execution Contract Test")
    print("=" * 90)
    builder = ControlledExecutionContract()
    contract = builder.build_contract()
    desc = builder.describe_execution()
    check("Version", contract["version"] == "TE-v4.4")
    check("Default Disabled", contract["default_mode"] == "disabled")
    check("Explicit Opt In", contract["activation_mode"] == "explicit_opt_in_only")
    check("Single Chunk", contract["allowed_scope"] == "single_chunk")
    check("Guarded Replacement", contract["result_replacement_mode"] == "guarded_controlled_only")
    check("Original Preserved", contract["original_result_preserved"] is True)
    check("No Provider Request", contract["real_provider_request_allowed"] is False)
    check("No Provider Fallback", contract["provider_fallback_allowed"] is False)
    check("No Real Translation", contract["real_translation_allowed"] is False)
    check("Required Freezes", set(contract["required_freezes"]) == {"TE-v4.0", "TE-v4.1", "TE-v4.2", "TE-v4.3"})
    check("Contract Valid", builder.validate_contract(contract))
    check("Description Valid", desc["replacement_requires_guard"] is True and desc["rollback_available"] is True)
    print("NTPE TE-v4.4 Stage-4.4.1 Controlled Execution Contract PASS")


if __name__ == "__main__":
    main()
