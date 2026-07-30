from core.translation_quality_v5 import QualityRepairPipeline


def check(name, condition):
    print(f"{name:<54} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v5.1 Stage-5.1.5 Boundary Regression Test")
    print("=" * 86)

    pipeline = QualityRepairPipeline()
    source = "문장 하나. 문장 둘. 문장 셋. 문장 넷."

    result = pipeline.run(
        source,
        "문장。",
        runtime_state={
            "attempt": 0,
            "max_attempts": 3,
            "timeout_seconds": 180,
            "chunk_size": 100,
        },
        config={"chunk_size": 100, "min_chunk_size": 20},
    )

    check("Quality Failure Detected", result["accepted"] is False)
    check("Retry Planned", result["retry_result"]["retry"] is True)
    check("Source Not Retained", result["source_text_retained"] is False)
    check("Translation Not Retained Flag", result["translated_text_retained"] is False)
    check("Provider Not Called", result["integration_status"]["provider_called"] is False)
    check("HTTP Not Called", result["integration_status"]["http_called"] is False)
    check("API Key Not Accessed", result["integration_status"]["api_key_accessed"] is False)
    check("Runtime Unchanged", result["integration_status"]["runtime_modified"] is False)
    check("Launcher Unchanged", result["integration_status"]["launcher_modified"] is False)
    check("Real Translation Not Executed", result["integration_status"]["real_translation_executed"] is False)
    check("Pipeline Valid", pipeline.validate_result(result))

    print("NTPE TE-v5.1 Stage-5.1.5 Boundary Regression PASS")


if __name__ == "__main__":
    main()
