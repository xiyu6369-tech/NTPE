
from core.translation_reliability import RetryStrategyBenchmark


def check(name, condition):
    print(f"{name:<46} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.0 Stage-4.0.5 Retry Strategy Benchmark Test")
    print("=" * 80)

    benchmark = RetryStrategyBenchmark()
    cases = [
        {
            "case_id": "success",
            "outcome": "success",
            "latency_ms": 50000,
            "attempts_needed": 1,
            "fixed_recoverable": True,
            "adaptive_recoverable": True,
        },
        {
            "case_id": "503-capacity",
            "outcome": "http_503",
            "latency_ms": 180000,
            "attempts_needed": 4,
            "fixed_recoverable": False,
            "adaptive_recoverable": True,
        },
        {
            "case_id": "timeout-split",
            "outcome": "read_timeout",
            "latency_ms": 180000,
            "attempts_needed": 4,
            "fixed_recoverable": False,
            "adaptive_recoverable": True,
            "chunk_size": 600,
            "source_text": "가" * 600,
        },
        {
            "case_id": "provider-zero",
            "outcome": "provider_not_attempted",
            "latency_ms": 1000,
            "attempts_needed": 4,
            "fixed_recoverable": False,
            "adaptive_recoverable": True,
        },
        {
            "case_id": "auth",
            "outcome": "authentication_error",
            "latency_ms": 1000,
            "attempts_needed": 1,
            "fixed_recoverable": False,
            "adaptive_recoverable": False,
        },
    ]

    report = benchmark.run(cases)
    fixed = report["fixed_strategy"]["summary"]
    adaptive = report["adaptive_strategy"]["summary"]
    comparison = report["comparison"]

    check("Cases Total", report["cases_total"] == 5)
    check("Fixed Success Count", fixed["success_count"] == 1)
    check("Adaptive Success Count", adaptive["success_count"] == 4)
    check("Success Rate Improved", comparison["success_rate_gain"] > 0)
    check("Split Recovery Counted", adaptive["split_recoveries"] >= 1)
    check("Provider Rebuild Counted", adaptive["provider_rebuild_recoveries"] >= 1)
    check("Adaptive Better", comparison["adaptive_better"] is True)
    check(
        "Recommendation",
        report["recommendation"] == "adopt_adaptive_retry_and_chunk_split",
    )

    adaptive_results = report["adaptive_strategy"]["results"]
    timeout_result = next(
        item for item in adaptive_results if item["case_id"] == "timeout-split"
    )
    provider_result = next(
        item for item in adaptive_results if item["case_id"] == "provider-zero"
    )
    auth_result = next(
        item for item in adaptive_results if item["case_id"] == "auth"
    )

    check("Timeout Uses Split", timeout_result["chunk_split"] is True)
    check("Provider Uses Rebuild", provider_result["provider_rebuild"] is True)
    check("Authentication Still Fails", auth_result["success"] is False)
    check("Report Valid", benchmark.validate_report(report))
    check("No Provider Call", report["safety"]["provider_called"] is False)
    check("No HTTP Call", report["safety"]["http_called"] is False)
    check("No API Key Access", report["safety"]["api_key_accessed"] is False)
    check("No Sleep Executed", report["safety"]["sleep_executed"] is False)
    check("No Runtime Modification", report["safety"]["runtime_modified"] is False)
    check("No Real Translation", report["safety"]["real_translation_executed"] is False)

    print("NTPE TE-v4.0 Stage-4.0.5 Retry Strategy Benchmark PASS")


if __name__ == "__main__":
    main()
