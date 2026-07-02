from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark.benchmark_registry import BenchmarkRegistry
from benchmark.benchmark_runner import BenchmarkRunner
from benchmark.benchmark_suite import BenchmarkSuite
from benchmark.benchmark_case import FunctionBenchmarkCase
from benchmark.stress import (
    CheckpointValidator,
    FailureInjector,
    MemoryMonitor,
    SoakRunner,
    StressRunner,
    build_failure_injector,
    build_stress_report,
    generate_workload,
    get_stress_benchmark_manifest,
    run_soak_benchmark,
    run_stress_benchmark,
    validate_checkpoint,
    write_stress_report,
)


def show(name: str, ok: bool) -> None:
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise AssertionError(name)


def main() -> None:
    workload = generate_workload(segment_count=12)
    show("Workload Generator", workload.size() == 12 and workload.total_chars() > 0)

    stress_result = StressRunner(workload=workload).run()
    show("Stress Runner", stress_result.is_passed() and stress_result.metrics["segments"] == 12)

    soak_result = SoakRunner(iterations=2, segment_count=5).run()
    show("Soak Runner", soak_result.is_passed() and soak_result.metrics["segments"] == 10)

    injector = build_failure_injector(fail_every=3, count=10)
    injected_result = StressRunner(workload=generate_workload(10), failure_injector=injector).run()
    show("Failure Injection", injected_result.is_passed() and injected_result.metrics["injected_failures"] > 0)

    monitor = MemoryMonitor()
    monitor.sample("a")
    _ = [str(i) for i in range(10)]
    monitor.sample("b")
    trend = monitor.trend()
    monitor.stop()
    show("Memory Monitor", trend["samples"] >= 2 and "peak_bytes" in trend)

    validator = CheckpointValidator()
    checkpoint = validator.build_checkpoint(["a", "b"])
    validation = validator.validate(checkpoint, expected_ids=["a", "b"])
    show("Checkpoint Validator", validation.valid and validation.processed == 2)

    report = build_stress_report([stress_result, soak_result])
    show("Stress Report", report["status"] == "PASS" and report["count"] == 2)

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "stress_report.json"
        written = write_stress_report([stress_result], path)
        loaded = json.loads(path.read_text(encoding="utf-8"))
        show("JSON Report", written["status"] == "PASS" and loaded["type"] == "stress_soak_report")

    registry = BenchmarkRegistry()
    registry.register(FunctionBenchmarkCase("stress_case", lambda ctx: run_stress_benchmark(3).metrics))
    show("Benchmark Registry", "stress_case" in registry.list())

    suite = BenchmarkSuite(name="stress_suite")
    suite.add(FunctionBenchmarkCase("soak_case", lambda ctx: run_soak_benchmark(1, 2).metrics))
    suite_results = BenchmarkRunner().run_suite(suite)
    show("Benchmark Suite", len(suite_results) == 1 and suite_results[0].is_passed())

    manifest = get_stress_benchmark_manifest()
    show("Stress Manifest", manifest["stage"] == "beta-stage-05.3" and manifest["backward_compatible"])

    show("Helper Functions", validate_checkpoint({"processed_ids": ["x"], "processed_count": 1}, ["x"]).valid)
    show("Integration Test", run_stress_benchmark(4).is_passed() and run_soak_benchmark(1, 4).is_passed())
    show("Regression Test", stress_result.metrics["segments_per_second"] > 0)
    show("Foundation Compatible", manifest["foundation_compatible"] is True)
    show("Backward Compatible", manifest["backward_compatible"] is True)
    print("PASS")


if __name__ == "__main__":
    main()
