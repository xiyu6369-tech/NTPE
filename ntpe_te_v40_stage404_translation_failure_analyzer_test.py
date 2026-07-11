
from core.translation_reliability import (
    TranslationReliabilityBaseline,
    TranslationFailureAnalyzer,
)


def check(name, condition):
    print(f"{name:<44} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.0 Stage-4.0.4 Translation Failure Analyzer Test")
    print("=" * 78)

    baseline = TranslationReliabilityBaseline()
    analyzer = TranslationFailureAnalyzer()

    samples = [
        {
            "chunk_index": 1,
            "provider": "nvidia",
            "model": "meta/llama-3.3-70b-instruct",
            "source_chars": 600,
            "translated_chars": 580,
            "latency_ms": 50000,
            "retry_count": 0,
            "provider_attempts": 1,
            "outcome": "success",
        },
        {
            "chunk_index": 2,
            "provider": "nvidia",
            "model": "meta/llama-3.3-70b-instruct",
            "source_chars": 600,
            "translated_chars": 0,
            "latency_ms": 180000,
            "retry_count": 2,
            "provider_attempts": 2,
            "outcome": "http_503",
        },
        {
            "chunk_index": 3,
            "provider": "nvidia",
            "model": "meta/llama-3.3-70b-instruct",
            "source_chars": 600,
            "translated_chars": 0,
            "latency_ms": 180000,
            "retry_count": 3,
            "provider_attempts": 3,
            "outcome": "http_503",
        },
        {
            "chunk_index": 4,
            "provider": "nvidia",
            "model": "meta/llama-3.3-70b-instruct",
            "source_chars": 600,
            "translated_chars": 0,
            "latency_ms": 0,
            "retry_count": 0,
            "provider_attempts": 0,
            "outcome": "provider_not_attempted",
        },
        {
            "chunk_index": 5,
            "provider": "nvidia",
            "model": "meta/llama-3.3-70b-instruct",
            "source_chars": 600,
            "translated_chars": 100,
            "latency_ms": 90000,
            "retry_count": 1,
            "provider_attempts": 1,
            "outcome": "too_short",
        },
    ]

    report = baseline.build_report(samples)
    analysis = analyzer.analyze(report)

    check("Total Events", analysis["summary"]["total_events"] == 5)
    check("Total Failures", analysis["summary"]["total_failures"] == 4)
    check("Distinct Failure Types", analysis["summary"]["distinct_failure_types"] == 3)
    check("Top Failure Exists", analysis["summary"]["top_failure"] is not None)
    check("Ranking Count", len(analysis["failure_ranking"]) == 3)
    check("Priority Count", len(analysis["priority_actions"]) == 3)
    check("First Priority Number", analysis["priority_actions"][0]["priority"] == 1)
    check("503 Counted", any(
        item["outcome"] == "http_503" and item["count"] == 2
        for item in analysis["failure_ranking"]
    ))
    check("Provider Not Attempted Counted", any(
        item["outcome"] == "provider_not_attempted"
        and item["provider_attempts_zero"] == 1
        for item in analysis["failure_ranking"]
    ))
    check("Retries Aggregated", analysis["diagnostics"]["total_retries"] == 6)
    check("Attempts Zero Aggregated", analysis["diagnostics"]["provider_attempts_zero_total"] == 1)
    check("Max Latency", analysis["diagnostics"]["max_latency_ms"] == 180000)
    check("Analysis Valid", analyzer.validate_analysis(analysis))
    check("No Provider Modification", analysis["safety"]["provider_runtime_modified"] is False)
    check("No HTTP Call", analysis["safety"]["http_called"] is False)
    check("No API Key Access", analysis["safety"]["api_key_accessed"] is False)
    check("No Real Translation", analysis["safety"]["real_translation_executed"] is False)

    empty = analyzer.analyze({"events": []})
    check("Empty Analysis Valid", analyzer.validate_analysis(empty))
    check("Empty Top Failure", empty["summary"]["top_failure"] is None)

    print("NTPE TE-v4.0 Stage-4.0.4 Translation Failure Analyzer PASS")


if __name__ == "__main__":
    main()
