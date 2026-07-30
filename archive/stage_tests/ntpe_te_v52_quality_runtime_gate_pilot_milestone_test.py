from core.translation_quality_v5 import (
    QualityRuntimeGateContract,
    QualityRuntimeGateAdmission,
    QualityRuntimeGateDecision,
    QualityRuntimeGatePilot,
)


def check(name, condition):
    print(f"{name:<54} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v5.2 Quality Runtime Gate Pilot Milestone Test")
    print("=" * 90)

    contract_builder = QualityRuntimeGateContract()
    admission = QualityRuntimeGateAdmission()
    decision = QualityRuntimeGateDecision()
    pilot = QualityRuntimeGatePilot()

    contract = contract_builder.build_contract()
    check("Contract Valid", contract_builder.validate_contract(contract))
    check("Contract Disabled Default", contract["default_mode"] == "disabled")
    check("Describe Gate", contract_builder.describe_gate()["rollback_available"] is True)

    request = {
        "caller": "translation_runtime",
        "gate_mode": "single_chunk_quality_gate",
        "runtime_id": "demo-v52",
        "chunk_index": 1,
        "chunk_count": 1,
    }
    flag = {"enabled": True, "mode": "single_chunk_quality_gate"}

    admitted = admission.evaluate(request, contract, flag)
    check("Admission Passed", admitted["admitted"] is True)
    check("Admission Valid", admission.validate_result(admitted))

    rejected = admission.evaluate(request, contract, {"enabled": False, "mode": "single_chunk_quality_gate"})
    check("Disabled Flag Rejected", rejected["admitted"] is False)

    forbidden = admission.evaluate(
        {**request, "metadata": {"api_key": "secret"}},
        contract,
        flag,
    )
    check("Forbidden Input Rejected", forbidden["admitted"] is False)

    source = (
        "정태의는 문을 열었다. 그는 카일을 바라보았다.\n\n"
        "카일은 조용히 웃었다. 그리고 다시 책을 펼쳤다."
    )
    good = (
        "鄭泰義打開了門。他望向凱爾。\n\n"
        "凱爾安靜地笑了笑，接著再次翻開書本。"
    )
    terms = {"정태의": "鄭泰義", "카일": "凱爾"}

    accepted_result = pilot.run(
        request,
        contract=contract,
        flag_state=flag,
        source_text=source,
        translated_text=good,
        locked_terms=terms,
    )
    check("Pilot Accept Status", accepted_result["status"] == "gate_accept")
    check("Pilot Accept Decision", accepted_result["gate_decision"]["decision"] == "accept")
    check("Pilot Accept Valid", pilot.validate_result(accepted_result))

    retry_result = pilot.run(
        request,
        contract=contract,
        flag_state=flag,
        source_text=source,
        translated_text="这个人가。",
        locked_terms=terms,
        runtime_state={
            "attempt": 0,
            "max_attempts": 5,
            "timeout_seconds": 180,
            "chunk_size": 600,
        },
        config={"chunk_size": 600, "min_chunk_size": 20},
    )
    check("Pilot Retry Status", retry_result["status"] == "gate_retry")
    check("Pilot Retry Decision", retry_result["gate_decision"]["decision"] == "retry")
    check("Pilot Retry Valid", pilot.validate_result(retry_result))

    blocked_result = pilot.run(
        request,
        contract=contract,
        flag_state={"enabled": False, "mode": "single_chunk_quality_gate"},
        source_text=source,
        translated_text=good,
    )
    check("Pilot Blocked Status", blocked_result["status"] == "gate_blocked")
    check("Pilot Blocked Valid", pilot.validate_result(blocked_result))

    check("Decision Should Accept", decision.should_accept(accepted_result["gate_decision"]) is True)
    check("Runtime Result Unchanged", retry_result["runtime_result_unchanged"] is True)
    check("No Provider Call", retry_result["gate_decision"]["provider_called"] is False)
    check("No Real Translation", retry_result["gate_decision"]["real_translation_executed"] is False)

    print("NTPE TE-v5.2 Quality Runtime Gate Pilot Milestone PASS")


if __name__ == "__main__":
    main()
