from core.translation_reliability import RuntimeHookResultMapper


def check(name, condition):
    print(f"{name:<58} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.3 Stage-4.3.4 Runtime Hook Result Mapper Test")
    print("=" * 86)
    mapper = RuntimeHookResultMapper()
    hook_result = {
        "status": "shadow_hook_completed",
        "completed": True,
        "callback_called": True,
        "shadow_result": {
            "recovery_recommended": True,
            "recommended_action": "split_and_retry",
        },
    }

    mapping = mapper.map_result("runtime-434", hook_result, metadata={"source_text": "raw", "safe": True})
    check("Recommendation Available", mapping["status"] == "shadow_recommendation_available")
    check("Recovery Recommended", mapping["recovery_recommended"] is True)
    check("No Replacement", mapping["result_replacement_allowed"] is False)
    check("Original Unchanged", mapping["original_runtime_result_unchanged"] is True)
    check("No Provider Request", mapping["real_provider_request_executed"] is False)
    check("Metadata Sanitized", "raw" not in str(mapping["metadata"]) and "source_text" not in str(mapping["metadata"]))
    check("Should Not Replace", mapper.should_replace_runtime_result(mapping) is False)
    check("Mapping Valid", mapper.validate_mapping(mapping))

    no_action = mapper.map_result("runtime-434", {"status": "shadow_hook_completed", "completed": True, "shadow_result": {}})
    check("No Action", no_action["status"] == "shadow_no_action")
    check("No Action Valid", mapper.validate_mapping(no_action))

    failed = mapper.map_result("runtime-434", {"status": "shadow_hook_failed"})
    check("Failure Mapping", failed["status"] == "shadow_hook_failed")
    check("Failure Valid", mapper.validate_mapping(failed))

    rolled = mapper.map_result("runtime-434", hook_result, {"rolled_back": True, "status": "rolled_back", "current_mode": "disabled"})
    check("Rollback Mapping", rolled["status"] == "shadow_rolled_back")
    check("Rollback Valid", mapper.validate_mapping(rolled))
    print("NTPE TE-v4.3 Stage-4.3.4 Runtime Hook Result Mapper PASS")


if __name__ == "__main__":
    main()
