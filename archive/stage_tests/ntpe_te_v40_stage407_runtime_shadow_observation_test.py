
from core.translation_reliability import RuntimeShadowObservation


def check(name, condition):
    print(f"{name:<48} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.0 Stage-4.0.7 Runtime Shadow Observation Test")
    print("=" * 82)

    observer = RuntimeShadowObservation()

    disabled = observer.observe([
        {
            "chunk_index": 1,
            "source_text": "가" * 600,
            "translated_text": "譯" * 580,
            "provider_attempts": 1,
            "outcome": "success",
        }
    ])
    check("Default Disabled", disabled["status"] == "disabled")
    check("Disabled Has No Adapter Result", disabled["adapter_result"] == {})
    check("Disabled Result Valid", observer.validate_result(disabled))

    events = [
        {
            "chunk_index": 1,
            "provider": "nvidia",
            "model": "meta/llama-3.3-70b-instruct",
            "source_text": "가" * 600,
            "translated_text": "譯" * 580,
            "latency_ms": 50000,
            "retry_count": 0,
            "provider_attempts": 1,
            "http_status": 200,
            "outcome": "success",
        },
        {
            "chunk_index": 2,
            "provider": "nvidia",
            "model": "meta/llama-3.3-70b-instruct",
            "source_text": "가" * 600,
            "translated_text": "",
            "latency_ms": 180000,
            "retry_count": 1,
            "provider_attempts": 1,
            "http_status": 503,
            "outcome": "http_503",
            "api_key": "must-not-retain",
        },
        {
            "chunk_index": 3,
            "provider": "nvidia",
            "model": "meta/llama-3.3-70b-instruct",
            "source_chars": 600,
            "translated_chars": 0,
            "latency_ms": 0,
            "retry_count": 0,
            "provider_attempts": 0,
            "outcome": "provider_not_attempted",
        },
    ]

    result = observer.observe(events, {"enabled": True})

    check("Shadow Observation Completed", result["status"] == "shadow_observation_completed")
    check("Shadow Mode Enabled", result["shadow_mode"] is True)
    check("Events Observed", result["observation_summary"]["events_observed"] == 3)
    check("Failure Events Counted", result["observation_summary"]["failure_events"] == 2)
    check("503 Counted", result["outcome_breakdown"]["http_503"] == 1)
    check("Provider Zero Counted", result["observation_summary"]["provider_attempts_zero"] == 1)
    check("Provider Breakdown", result["provider_breakdown"]["nvidia"] == 3)
    check("Model Breakdown", result["model_breakdown"]["meta/llama-3.3-70b-instruct"] == 3)
    check("Recommendations Generated", len(result["shadow_recommendations"]) >= 1)
    check("Recommendations Are Shadow Only", all(
        item["shadow_only"] is True
        and item["execute_automatically"] is False
        for item in result["shadow_recommendations"]
    ))

    payload = str(result)
    check("API Key Not Retained", "must-not-retain" not in payload)
    check("Source Text Not Retained", "source_text" not in str(result["adapter_result"]["baseline_report"]["events"]))
    check("Result Valid", observer.validate_result(result))
    check("Read Only", result["integration_status"]["read_only"] is True)
    check("No Runtime Modification", result["integration_status"]["runtime_modified"] is False)
    check("No Provider Call", result["integration_status"]["provider_called"] is False)
    check("No Retry Execution", result["integration_status"]["retry_executed"] is False)
    check("No Split Execution", result["integration_status"]["split_executed"] is False)
    check("No Real Translation", result["integration_status"]["real_translation_executed"] is False)

    print("NTPE TE-v4.0 Stage-4.0.7 Runtime Shadow Observation PASS")


if __name__ == "__main__":
    main()
