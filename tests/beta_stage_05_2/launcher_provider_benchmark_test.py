from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark import BenchmarkContext, BenchmarkRegistry, BenchmarkRunner, BenchmarkSuite, FunctionBenchmarkCase
from benchmark.report_writer import JSONBenchmarkReportWriter
from benchmark.provider import (
    FallbackBenchmark,
    HealthBenchmark,
    LatencyBenchmark,
    ProviderBenchmark,
    ProviderBenchmarkMetrics,
    RateLimitBenchmark,
    RetryBenchmark,
    ThroughputBenchmark,
    attach_provider_benchmark_manifest,
    build_provider_benchmark_manifest,
    run_latency_benchmark,
    run_provider_benchmark,
    run_throughput_benchmark,
    summarize_provider_metrics,
)
from core.ai_provider.contracts import MockProvider
from core.ai_provider.fallback import FallbackStrategy
from core.ai_provider.manager import ProviderManager
from core.ai_provider.rate_limiter import RateLimiter
from core.ai_provider.registry import ProviderRegistry
from core.ai_provider.retry import RetryPolicy
from core.ai_provider.router import ProviderRouter


def show(name: str, ok: bool) -> None:
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise AssertionError(name)


def build_manager(provider=None, default=True, **kwargs):
    registry = ProviderRegistry()
    registry.register(provider or MockProvider(name="mock", response_text="translated {prompt}"), default=default)
    return ProviderManager(registry=registry, **kwargs)


def main() -> None:
    output_dir = ROOT / "tmp" / "benchmark_stage_05_2"
    context = BenchmarkContext(output_dir=output_dir, metadata={"stage": "05.2"})

    provider = MockProvider(name="latency_mock", response_text="translated {prompt}")
    latency_results = LatencyBenchmark(provider=provider, prompts=["a", "b", "c"]).run(context)
    show("Provider Benchmark", len(run_provider_benchmark(provider=provider, prompts=["x", "y"])) == 3)
    show("Latency Benchmark", latency_results[0].metrics["requests"] == 3 and latency_results[0].metrics["avg_latency_ms"] >= 0)

    throughput_results = ThroughputBenchmark(provider=MockProvider(name="throughput_mock", response_text="one two three {prompt}"), prompts=["a", "b", "c", "d"]).run()
    show("Throughput Benchmark", throughput_results[0].metrics["requests_per_minute"] > 0 and throughput_results[0].metrics["tokens_per_second"] > 0)

    retry_provider = MockProvider(name="retry_mock", response_text="retry ok", fail_times=2, retryable=True)
    retry_manager = build_manager(retry_provider, retry_policy=RetryPolicy(max_attempts=3))
    retry_results = RetryBenchmark(retry_manager).run()
    show("Retry Benchmark", retry_results[0].metrics["retry_count"] == 2 and retry_results[0].metrics["retry_success"] is True)

    primary = MockProvider(name="primary", response_text="fail", fail_times=5, retryable=True)
    backup = MockProvider(name="backup", response_text="backup ok")
    fallback_registry = ProviderRegistry()
    fallback_registry.register(primary, default=True)
    fallback_registry.register(backup)
    fallback_manager = ProviderManager(
        registry=fallback_registry,
        router=ProviderRouter(default_provider="primary"),
        retry_policy=RetryPolicy(max_attempts=1),
        fallback=FallbackStrategy(["backup"]),
    )
    fallback_results = FallbackBenchmark(fallback_manager).run()
    show("Fallback Benchmark", fallback_results[0].metrics["fallback_triggered"] is True and fallback_results[0].metrics["provider"] == "backup")

    rate_limited_manager = build_manager(
        MockProvider(name="limited", response_text="ok"),
        rate_limiter=RateLimiter(max_calls=1, window_seconds=60),
    )
    rate_results = RateLimitBenchmark(rate_limited_manager, attempts=3).run()
    show("Rate Limit Benchmark", rate_results[0].metrics["attempts"] == 3 and rate_results[0].metrics["rate_limited"] >= 1)

    manager = build_manager(MockProvider(name="health", response_text="ok"))
    health_results = HealthBenchmark(manager).run()
    show("Health Benchmark", health_results[0].metrics["providers"] == 1 and health_results[0].metrics["availability"] == 1.0)

    bag = ProviderBenchmarkMetrics()
    bag.record_success(10, "hello world")
    bag.record_failure(20)
    bag.retries = 1
    summary = summarize_provider_metrics(bag)
    show("Provider Metrics", summary["requests"] == 2 and summary["success_rate"] == 0.5 and summary["p95_latency_ms"] >= 10)

    helper_results = []
    helper_results.extend(run_latency_benchmark(MockProvider(name="hlat", response_text="ok"), ["a"]))
    helper_results.extend(run_throughput_benchmark(MockProvider(name="hthr", response_text="ok"), ["a", "b"]))
    helper_results.extend(run_provider_benchmark(provider=MockProvider(name="hall", response_text="ok"), prompts=["a"]))
    show("Helper Functions", len(helper_results) == 5 and all(r.is_passed() for r in helper_results))

    registry = BenchmarkRegistry()
    registry.register(FunctionBenchmarkCase("provider_latency_case", lambda ctx: latency_results[0].metrics))
    registry.register(FunctionBenchmarkCase("provider_throughput_case", lambda ctx: throughput_results[0].metrics))
    runner = BenchmarkRunner(context)
    registry_results = runner.run_registry(registry)
    show("Benchmark Registry", len(registry_results) == 2 and all(r.is_passed() for r in registry_results))

    suite = BenchmarkSuite("provider_suite")
    suite.add(FunctionBenchmarkCase("provider_retry_case", lambda ctx: retry_results[0].metrics))
    suite.add(FunctionBenchmarkCase("provider_fallback_case", lambda ctx: fallback_results[0].metrics))
    suite_results = runner.run_suite(suite)
    show("Integration Test", len(suite_results) == 2 and all(r.is_passed() for r in suite_results))

    all_results = latency_results + throughput_results + retry_results + fallback_results + rate_results + health_results + registry_results + suite_results
    report_path = JSONBenchmarkReportWriter().write(
        all_results,
        output_dir / "provider_benchmark.json",
        metadata={"stage": "beta-stage-05.2"},
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    show("JSON Report", payload["summary"]["total"] == len(all_results) and payload["summary"]["failed"] == 0)

    manifest = build_provider_benchmark_manifest()
    show("Provider Manifest", manifest["stage"] == "beta-stage-05.2" and "provider_latency" in manifest["capabilities"])
    attached = attach_provider_benchmark_manifest({"runtime": "ok"})
    show("Manifest Helper", attached["provider_benchmark"]["name"] == "ntpe.provider.benchmark")

    # Regression-ready means the JSON report is deterministic and includes metrics for future comparison.
    show("Regression Test", payload["metadata"]["stage"] == "beta-stage-05.2" and len(payload["results"]) >= 8)
    show("Backward Compatible", manifest["foundation_compatibility"] == "foundation-v1.0-frozen")
    print("PASS")


if __name__ == "__main__":
    main()
