"""NTPE 1.0 Beta Stage-09.3 Task Queue test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflow import (  # noqa: E402
    WorkflowCore,
    JobScheduler,
    PipelineOrchestrator,
    WorkflowTaskQueue,
    TaskPriority,
    TaskStatus,
    TASK_QUEUE_STAGE,
)
from integration import EventBus, ServiceContainer, build_freeze_manifest, validate_freeze_manifest  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("NTPE 1.0 Beta Stage-09.3 Task Queue Test")
    print("=" * 72)

    bus = EventBus()
    container = ServiceContainer(metadata={"stage": "09.3"})
    container.register_instance("prefix", "translated")

    workflow_core = WorkflowCore(event_bus=bus, service_container=container, metadata={"stage": "09.3"})
    workflow = workflow_core.create_workflow("task-workflow")
    workflow.add_step("load", lambda context, payload, services: payload.get("text", ""))
    workflow.add_step("translate", lambda context, payload, services: f"{services.resolve('prefix')}:{context.get('load')}", depends_on=["load"])

    scheduler = JobScheduler(event_bus=bus, service_container=container, workflow_core=workflow_core, metadata={"stage": "09.3"})
    orchestrator = PipelineOrchestrator(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=scheduler, metadata={"stage": "09.3"})
    pipeline = orchestrator.create_pipeline("task-pipeline")
    orchestrator.add_stage("task-pipeline", "normalize", lambda context, payload, services: payload["text"].strip())

    queue = WorkflowTaskQueue(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=scheduler, pipeline_orchestrator=orchestrator, metadata={"stage": "09.3"})

    def echo(context, payload, services):
        context.set("seen", True)
        return f"echo:{payload['text']}"

    low = queue.enqueue_task("low", echo, payload={"text": "low"}, priority=TaskPriority.LOW)
    high = queue.enqueue_task("high", echo, payload={"text": "high"}, priority=TaskPriority.HIGH)
    first = queue.run_next()
    second = queue.run_next()

    check("Task Created", low.name == "low" and high.name == "high")
    check("Task Priority", first.task_id == high.task_id and second.task_id == low.task_id)
    check("Task Dispatch", first.ok and first.output == "echo:high")
    check("Task Result", second.ok and second.output == "echo:low")
    check("Task Status", queue.status(high.task_id) == TaskStatus.COMPLETED.value)

    attempts = {"n": 0}
    def flaky(context, payload, services):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("retry-me")
        return "recovered"

    retry_task = queue.enqueue_task("flaky", flaky, max_retries=1)
    retry_result = queue.run_next()
    check("Task Retry", retry_result.ok and retry_result.output == "recovered" and retry_result.attempts == 2)

    cancel_task = queue.enqueue_task("cancel", echo, payload={"text": "x"})
    queue.cancel(cancel_task.task_id)
    cancel_result = queue.run_next()
    check("Task Cancellation", cancel_result.status == TaskStatus.CANCELLED)

    failed = queue.enqueue_task("fail", lambda context, payload, services: (_ for _ in ()).throw(RuntimeError("boom")))
    failed_result = queue.run_next()
    check("Task Failure", failed_result.status == TaskStatus.FAILED and failed_result.error == "boom")

    wf_task = queue.enqueue_task("workflow-task", workflow_name="task-workflow", payload={"text": "chapter"})
    wf_result = queue.run_next()
    check("Workflow Integration", wf_result.ok and wf_result.output.outputs["translate"] == "translated:chapter")

    job = scheduler.schedule_job("queued-job", echo, payload={"text": "job"})
    linked_task = queue.enqueue_task("linked-job-task", job_id=job.job_id)
    linked_result = queue.run_next()
    check("Job Scheduler Bridge", linked_result.ok and linked_result.output["job_id"] == job.job_id)

    pipe_task = queue.enqueue_task("linked-pipeline-task", pipeline_id=pipeline.pipeline_id)
    pipe_result = queue.run_next()
    check("Pipeline Bridge", pipe_result.ok and pipe_result.output["pipeline_id"] == pipeline.pipeline_id)

    metrics = queue.metrics()
    manifest = queue.manifest()
    freeze = validate_freeze_manifest(build_freeze_manifest({"stage": "09.3"}))

    check("Queue Metrics", metrics["total"] >= 8 and metrics["completed"] >= 6 and metrics["failed"] >= 1 and metrics["cancelled"] >= 1)
    check("Queue Manifest", manifest["stage"] == TASK_QUEUE_STAGE and manifest["additive_only"] is True)
    check("Runtime Integration", manifest["bridges"]["service_container_attached"] is True)
    check("Event Dispatch", len([e for e in bus.history if "task" in e.get("event", {}).get("type", "")]) >= 8)
    check("Foundation Freeze", freeze.ok and freeze.status == "frozen")
    check("Backward Compatible", manifest["integration_status"] == "frozen" and manifest["workflow_core_compatible"] is True)

    print("PASS")


if __name__ == "__main__":
    main()
