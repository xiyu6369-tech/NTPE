
from core.translation_reliability import ReliabilityRuntimeIntegrationAdapter


def check(name, condition):
    print(f"{name:<48} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.0 Stage-4.0.6 Reliability Runtime Integration Adapter Test")
    print("=" * 86)

    adapter = ReliabilityRuntimeIntegrationAdapter()

    disabled = adapter.process(
        [
            {
                "chunk_index": 1,
                "source_text": "가" * 600,
                "translated_text": "譯" * 580,
                "provider_attempts": 1,
                "outcome": "success",
            }
        ]
    )
    check("Default Disabled", disabled["status"] == "disabled")
    check("Disabled Has No Analysis", disabled["baseline_report"] == {})
    check("Disabled Result Valid", adapter.validate_result(disabled))

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
            "metadata": {"profile": "literary"},
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
            "http_status": 200,
            "outcome": "read_timeout",
            "api_key": "must-not-retain",
            "metadata": {"source_text": "must-not-retain"},
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

    result = adapter.process(
        events,
        {
            "enabled": True,
            "chunk_size": 600,
            "min_chunk_size": 200,
            "timeout_seconds": 180,
        },
    )

    check("Analysis Completed", result["status"] == "analysis_completed")
    check("Events Counted", result["metadata"]["events_received"] == 3)
    check("Baseline Total", result["baseline_report"]["summary"]["total_chunks"] == 3)
    check("Failure Total", result["failure_analysis"]["summary"]["total_failures"] == 2)
    check("Retry Decisions Count", len(result["retry_decisions"]) == 2)
    check("Split Plans Count", len(result["split_plans"]) == 2)

    timeout_plan = next(
        item for item in result["split_plans"] if item["outcome"] == "read_timeout"
    )
    provider_decision = next(
        item for item in result["retry_decisions"]
        if item["outcome"] == "provider_not_attempted"
    )

    check("Timeout Split Planned", timeout_plan["plan"]["should_split"] is True)
    check("Segment Text Removed", all(
        "text" not in segment for segment in timeout_plan["plan"]["segments"]
    ))
    check(
        "Provider Rebuild Suggested",
        provider_decision["decision"]["rebuild_provider_session"] is True,
    )

    event_payload = str(result["baseline_report"]["events"])
    check("API Key Not Retained", "must-not-retain" not in event_payload)
    check("Source Text Not Retained", "source_text" not in event_payload)
    check("Adapter Result Valid", adapter.validate_result(result))
    check("No Runtime Modification", result["integration_status"]["runtime_modified"] is False)
    check("No Provider Call", result["integration_status"]["provider_called"] is False)
    check("No HTTP Call", result["integration_status"]["http_called"] is False)
    check("No API Key Access", result["integration_status"]["api_key_accessed"] is False)
    check("No Retry Execution", result["integration_status"]["retry_executed"] is False)
    check("No Split Execution", result["integration_status"]["split_executed"] is False)
    check(
        "No Real Translation",
        result["integration_status"]["real_translation_executed"] is False,
    )

    print("NTPE TE-v4.0 Stage-4.0.6 Reliability Runtime Integration Adapter PASS")


if __name__ == "__main__":
    main()
