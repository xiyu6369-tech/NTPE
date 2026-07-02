"""NTPE 1.0 Beta Stage-09.1 Job Scheduler test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflow import (  # noqa: E402
    WorkflowCore,
    WorkflowContext,
    JobScheduler,
    JobPriority,
    JobStatus,
    JOB_SCHEDULER_STAGE,
)
from integration import EventBus, ServiceContainer, build_freeze_manifest, validate_freeze_manifest  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("NTPE 1.0 Beta Stage-09.1 Job Scheduler Test")
    print("=" * 72)

    bus = EventBus()
    container = ServiceContainer(metadata={"stage": "09.1"})
    container.register_instance("prefix", "translated")
    workflow_core = WorkflowCore(event_bus=bus, service_container=container, metadata={"stage": "09.1"})
    workflow = workflow_core.create_workflow("job-flow")
    workflow.add_step("load", lambda context, payload, services: payload.get("text", ""))
    workflow.add_step("translate", lambda context, payload, services: f"{services.resolve('prefix')}:{context.get('load')}", depends_on=["load"])

    scheduler = JobScheduler(event_bus=bus, service_container=container, workflow_core=workflow_core, metadata={"stage": "09.1"})

    def echo(context, payload, services):
        context.set("seen", True)
        return f"echo:{payload['text']}"

    job = scheduler.create_job("echo", echo, payload={"text": "hello"}, priority=JobPriority.HIGH)
    scheduler.schedule(job)
    result = scheduler.run_next()

    check("Job Created", job.name == "echo" and scheduler.manager.registry.get(job.job_id) is job)
    check("Job Scheduled", result.job_id == job.job_id and len(scheduler.manager.queue) == 0)
    check("Job Priority", int(job.priority) == int(JobPriority.HIGH))
    check("Job Queue", scheduler.manager.queue.empty())
    check("Job Status", result.ok and scheduler.status(job.job_id) == JobStatus.COMPLETED.value)

    attempts = {"n": 0}
    def flaky(context, payload, services):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("retry-me")
        return "recovered"

    retry_job = scheduler.schedule_job("flaky", flaky, max_retries=1)
    retry_result = scheduler.run_next()
    check("Job Retry", retry_result.ok and retry_result.output == "recovered" and retry_result.attempts == 2)

    cancel_job = scheduler.schedule_job("cancel-me", echo, payload={"text": "x"})
    scheduler.cancel(cancel_job.job_id)
    cancel_result = scheduler.run_next()
    check("Job Cancel", cancel_result.status == JobStatus.CANCELLED)

    timeout_job = scheduler.schedule_job("timeout", echo, payload={"text": "x"}, timeout_seconds=0)
    timeout_result = scheduler.run_next()
    check("Job Timeout", timeout_result.status == JobStatus.TIMEOUT)

    failed = scheduler.schedule_job("fail", lambda context, payload, services: (_ for _ in ()).throw(RuntimeError("boom")))
    failed_result = scheduler.run_next()
    scheduler.resume(failed.job_id)
    resumed_result = scheduler.run_next()
    check("Job Resume", failed_result.status == JobStatus.FAILED and resumed_result.status == JobStatus.FAILED)

    wf_job = scheduler.schedule_job("workflow", workflow_name="job-flow", payload={"text": "book"})
    wf_result = scheduler.run_next()
    check("Workflow Integration", wf_result.ok and wf_result.output.outputs["translate"] == "translated:book")

    manifest = scheduler.manifest()
    freeze = validate_freeze_manifest(build_freeze_manifest({"stage": "09.1"}))
    check("Runtime Integration", manifest["bridges"]["service_container_attached"] is True)
    check("Event Dispatch", len(bus.history) >= 8)
    check("Scheduler Manifest", manifest["stage"] == JOB_SCHEDULER_STAGE and manifest["foundation_status"] == "frozen")
    check("Workflow Core Compatible", workflow_core.execute("job-flow", context=WorkflowContext(session_id="compat"), text="ok").ok)
    check("Foundation Freeze", freeze.ok and freeze.status == "frozen")
    check("Backward Compatible", manifest["additive_only"] is True and manifest["integration_status"] == "frozen")

    print("PASS")


if __name__ == "__main__":
    main()
