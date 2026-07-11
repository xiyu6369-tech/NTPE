from core.translation_quality_v5 import QualityRuntimeGateContract, QualityRuntimeGatePilot


def check(name, condition):
    print(f"{name:<54} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v5.2 Stage-5.2.5 Boundary Regression Test")
    print("=" * 86)

    contract = QualityRuntimeGateContract().build_contract()
    pilot = QualityRuntimeGatePilot()
    request = {
        "caller": "translation_runtime",
        "gate_mode": "single_chunk_quality_gate",
        "runtime_id": "boundary-v52",
        "chunk_index": 1,
        "chunk_count": 1,
    }

    result = pilot.run(
        request,
        contract=contract,
        flag_state={"enabled": True, "mode": "single_chunk_quality_gate"},
        source_text="문장 하나. 문장 둘. 문장 셋. 문장 넷.",
        translated_text="문장。",
        runtime_state={"attempt": 0, "max_attempts": 3, "timeout_seconds": 180, "chunk_size": 100},
        config={"chunk_size": 100, "min_chunk_size": 20},
    )

    check("Gate Retry Produced", result["status"] == "gate_retry")
    check("Runtime Result Unchanged", result["runtime_result_unchanged"] is True)
    check("Source Not Retained Flag", result["source_text_retained"] is False)
    check("Translation Not Retained Flag", result["translated_text_retained"] is False)
    check("Provider Not Called", result["gate_decision"]["provider_called"] is False)
    check("HTTP Not Called", result["gate_decision"]["http_called"] is False)
    check("API Key Not Accessed", result["gate_decision"]["api_key_accessed"] is False)
    check("Real Translation Not Executed", result["gate_decision"]["real_translation_executed"] is False)
    check("Pilot Valid", pilot.validate_result(result))

    print("NTPE TE-v5.2 Stage-5.2.5 Boundary Regression PASS")


if __name__ == "__main__":
    main()
