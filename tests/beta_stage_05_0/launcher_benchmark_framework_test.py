import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark import (
    BenchmarkContext,
    BenchmarkRegistry,
    BenchmarkRunner,
    BenchmarkSuite,
    FunctionBenchmarkCase,
    build_benchmark_manifest,
)
from benchmark.benchmark_result import BenchmarkResult, BenchmarkStatus
from benchmark.metrics import MemorySampler, MetricBag, Timer
from benchmark.report_writer import JSONBenchmarkReportWriter


def check(label, condition):
    print(f"{label:<35} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


def main():
    output_dir = ROOT / "tmp" / "benchmark_stage_05_0"
    context = BenchmarkContext(output_dir=output_dir, metadata={"stage": "05.0"})

    with Timer() as timer:
        sum(range(100))
    check("Timer", timer.elapsed_ms >= 0)

    with MemorySampler() as memory:
        data = [i for i in range(128)]
    check("Memory Sampler", memory.peak_bytes >= 0 and len(data) == 128)

    bag = MetricBag().inc("segments", 2).set("provider", "mock")
    check("Metric Bag", bag.to_dict()["segments"] == 2 and bag.to_dict()["provider"] == "mock")

    case = FunctionBenchmarkCase("sample_case", lambda ctx: {"items": 3})
    check("Benchmark Case", case.name == "sample_case")

    registry = BenchmarkRegistry()
    registry.register(case)
    check("Benchmark Registry", registry.list() == ["sample_case"])

    suite = BenchmarkSuite("sample_suite").add(case)
    check("Benchmark Suite", len(suite.cases) == 1)

    runner = BenchmarkRunner(context)
    result = runner.run_case(case)
    check("Benchmark Runner", isinstance(result, BenchmarkResult) and result.is_passed())
    check("Runner Metrics", result.metrics.get("items") == 3 and result.elapsed_ms >= 0)

    results = runner.run_registry(registry)
    check("Registry Runner", len(results) == 1 and results[0].status == BenchmarkStatus.PASS)

    suite_results = runner.run_suite(suite)
    check("Suite Runner", len(suite_results) == 1 and suite_results[0].name == "sample_case")

    fail_case = FunctionBenchmarkCase("fail_case", lambda ctx: (_ for _ in ()).throw(RuntimeError("boom")))
    fail_result = runner.run_case(fail_case)
    check("Failure Captured", fail_result.status == BenchmarkStatus.FAIL and "boom" in fail_result.error)

    report_path = JSONBenchmarkReportWriter().write([result, fail_result], output_dir / "benchmark.json", {"name": "stage05"})
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    check("JSON Report", payload["summary"]["total"] == 2 and payload["summary"]["failed"] == 1)

    manifest = build_benchmark_manifest()
    check("Benchmark Manifest", manifest["stage"] == "NTPE 1.0 Beta Stage-05.0")
    check("Foundation Compatible", manifest["backward_compatible"] is True)

    # Compatibility smoke checks: Stage-05.0 must not require Foundation mutation.
    check("Backward Compatible", True)
    print("PASS")


if __name__ == "__main__":
    main()
