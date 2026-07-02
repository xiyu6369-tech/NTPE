"""NTPE 1.0 Beta Stage-09.7 Workflow Benchmark test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark import (  # noqa: E402
    WORKFLOW_BENCHMARK_STAGE,
    WORKFLOW_BENCHMARK_VERSION,
    WorkflowBenchmark,
    WorkflowBenchmarkSuite,
    WorkflowLoadTest,
    WorkflowProfiler,
    WorkflowStressTest,
)
from integration import EventBus, ServiceContainer  # noqa: E402
from workflow import (  # noqa: E402
    create_distributed_coordinator,
    create_job_scheduler,
    create_pipeline_orchestrator,
    create_task_queue,
    create_worker_runtime,
    create_workflow_core,
    create_workflow_persistence,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("NTPE 1.0 Beta Stage-09.7 Workflow Benchmark Test")
    print("=" * 78)

    check("Workflow Benchmark", "Stage-09.7" in WORKFLOW_BENCHMARK_STAGE and WORKFLOW_BENCHMARK_VERSION == "0.9.7")

    bus = EventBus()
    container = ServiceContainer(metadata={"stage": "09.7"})
    workflow_core = create_workflow_core(event_bus=bus, service_container=container)
    job_scheduler = create_job_scheduler(event_bus=bus, service_container=container, workflow_core=workflow_core)
    pipeline = create_pipeline_orchestrator(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler)
    task_queue = create_task_queue(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler, pipeline_orchestrator=pipeline)
    worker_runtime = create_worker_runtime(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler, pipeline_orchestrator=pipeline, task_queue=task_queue, worker_count=2)
    persistence = create_workflow_persistence(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler, pipeline_orchestrator=pipeline, task_queue=task_queue, worker_runtime=worker_runtime)
    distributed = create_distributed_coordinator(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler, pipeline_orchestrator=pipeline, task_queue=task_queue, worker_runtime=worker_runtime, persistence=persistence)
    distributed.register_node("node-a", capacity=2)
    distributed.register_node("node-b", capacity=1)

    container.register_instance("workflow_core", workflow_core)
    container.register_instance("job_scheduler", job_scheduler)
    container.register_instance("pipeline_orchestrator", pipeline)
    container.register_instance("task_queue", task_queue)
    container.register_instance("worker_runtime", worker_runtime)
    container.register_instance("workflow_persistence", persistence)
    container.register_instance("distributed_coordinator", distributed)

    workflow_core.create_workflow("bench_workflow")
    workflow_core.add_step("bench_workflow", "normalize", lambda **kw: {"ok": True, "step": "normalize"})
    workflow_core.add_step("bench_workflow", "translate", lambda **kw: {"ok": True, "step": "translate"}, depends_on=["normalize"])

    pipeline.create_pipeline("bench_pipeline")
    pipeline.add_stage("bench_pipeline", "prepare", lambda **kw: {"stage": "prepare"})
    pipeline.add_stage("bench_pipeline", "execute", lambda **kw: {"stage": "execute"}, depends_on=["prepare"])

    benchmark = WorkflowBenchmark(metadata={"stage": "09.7", "scope": "workflow"})
    benchmark.add_case("workflow_create", lambda: workflow_core.create_workflow("bench_dynamic"), iterations=2, category="workflow")
    benchmark.add_case("workflow_execute", lambda: workflow_core.execute("bench_workflow"), iterations=3, category="workflow")
    benchmark.add_case("job_schedule", lambda: job_scheduler.schedule_job("bench_job", lambda **kw: {"job": True}), iterations=3, category="job")
    benchmark.add_case("pipeline_execute", lambda: pipeline.execute("bench_pipeline"), iterations=3, category="pipeline")
    benchmark.add_case("task_queue", lambda: task_queue.enqueue_task("bench_task", lambda **kw: {"task": True}), iterations=3, category="task")
    benchmark.add_case("worker_execute", lambda: worker_runtime.execute_task(worker_runtime.create_task("worker_task", lambda **kw: {"worker": True})), iterations=3, category="worker")
    benchmark.add_case("persistence_snapshot", lambda: persistence.snapshot_workflow("bench_snapshot"), iterations=2, category="persistence")
    benchmark.add_case("distributed_dispatch", lambda: distributed.distribute_task({"task": "distributed"}), iterations=2, category="distributed")
    report = benchmark.run()
    summary = report.summary()

    check("Workflow Performance", report.ok and summary["count"] == 8 and "workflow" in summary["categories"])
    check("Job Scheduler", any(item.category == "job" for item in report.metrics))
    check("Pipeline Performance", any(item.category == "pipeline" for item in report.metrics))
    check("Task Queue", any(item.category == "task" for item in report.metrics))
    check("Worker Runtime", any(item.category == "worker" for item in report.metrics))
    check("Persistence", any(item.category == "persistence" for item in report.metrics))
    check("Distributed Execution", any(item.category == "distributed" for item in report.metrics) and distributed.manifest()["nodes"]["node_count"] == 2)

    profiler = WorkflowProfiler()
    metric = profiler.profile("workflow_manifest", lambda: workflow_core.manifest(), iterations=2, category="profiler")
    check("Workflow Profiler", metric.passed and metric.throughput_ops_per_sec > 0)

    suite = WorkflowBenchmarkSuite("compat", metadata={"stage": "09.7"})
    suite.add("container_resolve", lambda: container.resolve("workflow_core"), iterations=2, category="compat")
    suite_report = suite.run()
    check("Workflow Suite", suite_report.ok and suite_report.summary()["count"] == 1)

    load = WorkflowLoadTest().run("task_load", lambda i: task_queue.enqueue_task(f"load_{i}", lambda **kw: {"i": i}), operations=5)
    check("Load Test", load["passed"] is True and load["iterations"] == 5 and load["stable"] is True)

    stress = WorkflowStressTest().run("workflow_stress", lambda: workflow_core.execute("bench_workflow"), cycles=5)
    check("Stress Test", stress["stable"] is True and stress["iterations"] == 5)

    check("Foundation Freeze", summary["foundation_status"] == "frozen")
    check("Backward Compatible", workflow_core.manifest()["foundation_status"] == "frozen" and pipeline.manifest()["integration_status"] == "frozen")

    print("PASS")


if __name__ == "__main__":
    main()
