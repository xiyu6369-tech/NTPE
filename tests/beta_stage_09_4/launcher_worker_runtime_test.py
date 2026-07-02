"""NTPE 1.0 Beta Stage-09.4 Worker Runtime test."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflow import (  # noqa: E402
    WorkflowCore,
    JobScheduler,
    PipelineOrchestrator,
    WorkflowTaskQueue,
    WorkerRuntime,
    WorkerStatus,
    WorkerRuntimeStatus,
    TaskPriority,
    TaskStatus,
    WORKER_RUNTIME_STAGE,
)
from integration import EventBus, ServiceContainer, build_freeze_manifest, validate_freeze_manifest  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("NTPE 1.0 Beta Stage-09.4 Worker Runtime Test")
    print("=" * 72)

    bus = EventBus()
    container = ServiceContainer(metadata={"stage": "09.4"})
    container.register_instance("prefix", "translated")

    workflow_core = WorkflowCore(event_bus=bus, service_container=container, metadata={"stage": "09.4"})
    workflow = workflow_core.create_workflow("worker-workflow")
    workflow.add_step("load", lambda context, payload, services: payload.get("text", ""))
    workflow.add_step("translate", lambda context, payload, services: f"{services.resolve('prefix')}:{context.get('load')}", depends_on=["load"])

    scheduler = JobScheduler(event_bus=bus, service_container=container, workflow_core=workflow_core, metadata={"stage": "09.4"})
    orchestrator = PipelineOrchestrator(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=scheduler, metadata={"stage": "09.4"})
    pipeline = orchestrator.create_pipeline("worker-pipeline")
    orchestrator.add_stage("worker-pipeline", "normalize", lambda context, payload, services: payload["text"].strip())

    queue = WorkflowTaskQueue(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=scheduler, pipeline_orchestrator=orchestrator, metadata={"stage": "09.4"})
    runtime = WorkerRuntime(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=scheduler, pipeline_orchestrator=orchestrator, task_queue=queue, worker_count=2, metadata={"stage": "09.4"})

    runtime.start()
    check("Worker Runtime", runtime.status == WorkerRuntimeStatus.RUNNING)
    check("Worker Pool", len(runtime.manager.pool) == 2)

    def echo(context, payload, services):
        context.set("seen", True)
        return f"echo:{payload['text']}"

    task = runtime.create_task("direct", echo, payload={"text": "direct"}, priority=TaskPriority.HIGH)
    result = runtime.execute_task(task)
    check("Worker Created", runtime.manager.registry.manifest()["count"] >= 2)
    check("Task Execution", result.ok and result.output == "echo:direct")
    check("Worker Lifecycle", any(worker.status == WorkerStatus.IDLE for worker in runtime.manager.pool.all()))

    attempts = {"n": 0}
    def flaky(context, payload, services):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("retry-me")
        return "recovered"

    retry_task = queue.enqueue_task("flaky", flaky, max_retries=1)
    retry_result = runtime.run_next()
    check("Worker Retry", retry_result.ok and retry_result.output == "recovered" and retry_result.attempts == 2)

    slow_task = runtime.create_task("slow", lambda context, payload, services: (time.sleep(0.01), "slow")[1])
    timeout_result = runtime.execute_task(slow_task, timeout=0.0)
    check("Worker Timeout", timeout_result.status == TaskStatus.FAILED and "timeout" in timeout_result.error)

    wf_task = queue.enqueue_task("workflow-task", workflow_name="worker-workflow", payload={"text": "chapter"})
    wf_result = runtime.run_next()
    check("Runtime Integration", wf_result.ok and wf_result.output.outputs["translate"] == "translated:chapter")

    job = scheduler.schedule_job("worker-job", echo, payload={"text": "job"})
    job_task = queue.enqueue_task("job-task", job_id=job.job_id)
    job_result = runtime.run_next()
    check("Pipeline Integration", job_result.ok and job_result.output["job_id"] == job.job_id)

    pipe_task = queue.enqueue_task("pipeline-task", pipeline_id=pipeline.pipeline_id)
    pipe_result = runtime.run_next()
    check("Task Queue Bridge", pipe_result.ok and pipe_result.output["pipeline_id"] == pipeline.pipeline_id)

    runtime.stop()
    check("Worker Stop", runtime.status == WorkerRuntimeStatus.STOPPED)

    manifest = runtime.manifest()
    freeze = validate_freeze_manifest(build_freeze_manifest({"stage": "09.4"}))
    check("Worker Manifest", manifest["stage"] == WORKER_RUNTIME_STAGE and manifest["additive_only"] is True)
    check("Event Bus Integration", len([e for e in bus.history if "worker" in e.get("event", {}).get("type", "")]) >= 8)
    check("Foundation Freeze", freeze.ok and freeze.status == "frozen")
    check("Backward Compatible", manifest["integration_status"] == "frozen" and manifest["task_queue_compatible"] is True)

    print("PASS")


if __name__ == "__main__":
    main()
