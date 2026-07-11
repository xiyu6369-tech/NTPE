
from core.translation_reliability import TranslationReliabilityBaseline


def check(name, condition):
    print(f"{name:<38} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.0 Stage-4.0.1 Translation Reliability Baseline Test")
    print("=" * 76)

    baseline = TranslationReliabilityBaseline()
    samples = [
        {
            "chunk_index": 1,
            "provider": "nvidia",
            "model": "meta/llama-3.3-70b-instruct",
            "source_text": "가" * 600,
            "translated_text": "譯" * 580,
            "latency_ms": 54000,
            "retry_count": 0,
            "provider_attempts": 1,
            "http_status": 200,
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
            "http_status": 503,
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
        },
        {
            "chunk_index": 4,
            "provider": "nvidia",
            "model": "meta/llama-3.3-70b-instruct",
            "source_text": "가" * 600,
            "translated_text": "短" * 100,
            "latency_ms": 90000,
            "retry_count": 1,
            "provider_attempts": 1,
            "http_status": 200,
        },
    ]

    report = baseline.build_report(samples)
    summary = report["summary"]

    check("Total Chunks", summary["total_chunks"] == 4)
    check("Success Chunks", summary["success_chunks"] == 1)
    check("Failed Chunks", summary["failed_chunks"] == 3)
    check("HTTP 503 Classified", report["failure_breakdown"]["http_503"] == 1)
    check("Provider Not Attempted", report["failure_breakdown"]["provider_not_attempted"] == 1)
    check("Too Short Classified", report["failure_breakdown"]["too_short"] == 1)
    check("Attempts Zero Count", summary["provider_attempts_zero"] == 1)
    check("Retries Counted", summary["total_retries"] == 3)
    check("Reliability Score", 0 <= summary["reliability_score"] <= 100)
    check("Provider Breakdown", report["provider_breakdown"]["nvidia"] == 4)
    check("No HTTP Call", report["safety"]["http_called"] is False)
    check("No API Key Access", report["safety"]["api_key_accessed"] is False)
    check("No Real Translation", report["safety"]["real_translation_executed"] is False)
    check("Report Valid", baseline.validate_report(report))

    print("NTPE TE-v4.0 Stage-4.0.1 Translation Reliability Baseline PASS")


if __name__ == "__main__":
    main()
