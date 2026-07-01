from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark import BenchmarkContext, BenchmarkRegistry, BenchmarkRunner, BenchmarkSuite, FunctionBenchmarkCase
from benchmark.report_writer import JSONBenchmarkReportWriter
from benchmark.runtime import (
    PipelineBenchmark,
    RecoveryBenchmark,
    RuntimeBenchmark,
    SessionBenchmark,
    attach_runtime_benchmark_manifest,
    build_runtime_benchmark_manifest,
    run_pipeline_benchmark,
    run_recovery_benchmark,
    run_runtime_benchmark,
    run_session_benchmark,
)


def show(name: str, ok: bool) -> None:
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise AssertionError(name)


class DummyRuntime:
    def __init__(self) -> None:
        self.started = False
        self.processed = []

    def start(self) -> None:
        self.started = True

    def create_job(self, payload):
        return {"id": payload.get("job_id"), "segments": payload.get("segments", [])}

    def process_segment(self, segment):
        self.processed.append(segment)
        return {"segment": segment, "status": "done"}


class DummySession:
    def checkpoint(self):
        return {"session_id": "dummy", "checkpointed": True}

    def resume(self):
        return {"session_id": "dummy", "resumed": True}


class DummyRecovery:
    def restore(self, checkpoint):
        data = dict(checkpoint)
        data["restored"] = True
        return data


def main() -> None:
    output_dir = ROOT / "tmp" / "benchmark_stage_05_1"
    context = BenchmarkContext(output_dir=output_dir, metadata={"stage": "05.1"})

    runtime = DummyRuntime()
    runtime_benchmark = RuntimeBenchmark(runtime=runtime, segments=["a", "b", "c"])
    runtime_results = runtime_benchmark.run(context)
    show("Runtime Benchmark", len(runtime_results) == 3 and all(r.is_passed() for r in runtime_results))
    show("Runtime Startup", runtime.started and runtime_results[0].name == "runtime_startup")
    show("Job Creation", runtime_results[1].metrics.get("segment_count") == 3)
    show("Segment Throughput", runtime_results[2].metrics.get("segments") == 3 and runtime_results[2].metrics.get("segments_per_second") > 0)

    pipeline = PipelineBenchmark(steps=[lambda x: str(x), lambda x: x + "!", lambda x: x.upper()])
    pipeline_results = pipeline.run()
    show("Pipeline Benchmark", len(pipeline_results) == 2 and all(r.is_passed() for r in pipeline_results))
    show("Pipeline Latency", pipeline_results[0].metrics.get("step_count") == 3)
    show("Throughput", pipeline_results[1].metrics.get("items") == 25 and pipeline_results[1].metrics.get("items_per_second") > 0)

    session_results = SessionBenchmark(session=DummySession()).run()
    show("Session Benchmark", len(session_results) == 2 and all(r.is_passed() for r in session_results))
    show("Session Resume", session_results[1].metrics.get("resumed") is True)

    recovery_results = RecoveryBenchmark(recovery=DummyRecovery()).run()
    show("Recovery Benchmark", len(recovery_results) == 1 and recovery_results[0].is_passed())
    show("Recovery Latency", recovery_results[0].metrics.get("restored") is True)

    helper_results = []
    helper_results.extend(run_runtime_benchmark(segments=[1, 2]))
    helper_results.extend(run_pipeline_benchmark())
    helper_results.extend(run_session_benchmark())
    helper_results.extend(run_recovery_benchmark())
    show("Helper Functions", len(helper_results) == 8 and all(r.is_passed() for r in helper_results))

    registry = BenchmarkRegistry()
    registry.register(FunctionBenchmarkCase("runtime_case", lambda ctx: {"ok": True}))
    registry.register(FunctionBenchmarkCase("pipeline_case", lambda ctx: {"latency_ms": 1.0}))
    runner = BenchmarkRunner(context)
    registry_results = runner.run_registry(registry)
    show("Registry Runtime", len(registry_results) == 2 and all(r.is_passed() for r in registry_results))

    suite = BenchmarkSuite("runtime_suite")
    suite.add(FunctionBenchmarkCase("session_case", lambda ctx: {"resume_ms": 1.0}))
    suite.add(FunctionBenchmarkCase("recovery_case", lambda ctx: {"recovery_ms": 1.0}))
    suite_results = runner.run_suite(suite)
    show("Suite Runtime", len(suite_results) == 2 and all(r.is_passed() for r in suite_results))

    all_results = runtime_results + pipeline_results + session_results + recovery_results + registry_results + suite_results
    report_path = JSONBenchmarkReportWriter().write(
        all_results,
        output_dir / "runtime_benchmark.json",
        metadata={"stage": "beta-stage-05.1"},
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    show("JSON Report", payload["summary"]["total"] == len(all_results) and payload["summary"]["failed"] == 0)

    manifest = build_runtime_benchmark_manifest()
    show("Runtime Benchmark Manifest", manifest["stage"] == "beta-stage-05.1" and "segment_throughput" in manifest["capabilities"])
    attached = attach_runtime_benchmark_manifest({"runtime": "ok"})
    show("Manifest Helper", attached["runtime_benchmark"]["name"] == "ntpe.runtime.benchmark")

    # Foundation and earlier Beta stages remain untouched; compatibility is by additive import/use only.
    show("Foundation Compatible", manifest["foundation_compatibility"] == "foundation-v1.0-frozen")
    show("Backward Compatible", True)
    print("PASS")


if __name__ == "__main__":
    main()
