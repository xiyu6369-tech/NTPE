"""NTPE 1.0 Beta Stage-09.2 Pipeline Orchestrator test."""
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
    PipelineContext,
    PipelineStatus,
    PIPELINE_ORCHESTRATOR_STAGE,
)
from integration import EventBus, ServiceContainer, build_freeze_manifest, validate_freeze_manifest  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("NTPE 1.0 Beta Stage-09.2 Pipeline Orchestrator Test")
    print("=" * 72)

    bus = EventBus()
    container = ServiceContainer(metadata={"stage": "09.2"})
    container.register_instance("prefix", "translated")

    workflow_core = WorkflowCore(event_bus=bus, service_container=container, metadata={"stage": "09.2"})
    workflow = workflow_core.create_workflow("pipe-workflow")
    workflow.add_step("wf-load", lambda context, payload, services: payload.get("text", ""))
    workflow.add_step("wf-translate", lambda context, payload, services: f"{services.resolve('prefix')}:{context.get('wf-load')}", depends_on=["wf-load"])

    scheduler = JobScheduler(event_bus=bus, service_container=container, workflow_core=workflow_core, metadata={"stage": "09.2"})
    orchestrator = PipelineOrchestrator(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=scheduler, metadata={"stage": "09.2"})

    pipeline = orchestrator.create_pipeline("translation-pipeline")
    orchestrator.add_stage("translation-pipeline", "load", lambda context, payload, services: payload["text"])
    orchestrator.add_stage("translation-pipeline", "normalize", lambda context, payload, services: context.get("load").strip(), depends_on=["load"])
    orchestrator.add_stage("translation-pipeline", "translate", lambda context, payload, services: f"{services.resolve('prefix')}:{context.get('normalize')}", depends_on=["normalize"])

    plan = orchestrator.build_plan("translation-pipeline")
    result = orchestrator.dispatcher.dispatch(pipeline, context=PipelineContext(pipeline_id=pipeline.pipeline_id), text=" book ")

    check("Pipeline Created", pipeline.name == "translation-pipeline")
    check("Pipeline Registered", orchestrator.registry.get("translation-pipeline") is pipeline)
    check("Execution Plan", plan.validate() and plan.names() == ["load", "normalize", "translate"])
    check("Stage Execution", result.ok and result.outputs["translate"] == "translated:book")
    check("Pipeline Context", result.stage_results["normalize"].ok and result.stage_results["translate"].ok)
    check("Pipeline Events", len([e for e in bus.history if "pipeline" in e.get("event", {}).get("type", "")]) >= 5)

    wf_pipeline = orchestrator.create_pipeline("workflow-pipeline")
    orchestrator.add_stage("workflow-pipeline", "runtime-workflow", workflow_name="pipe-workflow")
    wf_result = orchestrator.execute("workflow-pipeline", text="chapter")
    check("Runtime Integration", wf_result.ok and wf_result.outputs["runtime-workflow"].outputs["wf-translate"] == "translated:chapter")
    check("Workflow Integration", workflow_core.execute("pipe-workflow", text="compat").ok)

    job_pipeline = orchestrator.create_pipeline("job-pipeline")
    orchestrator.add_stage("job-pipeline", "job-stage", job_name="job-through-pipeline")
    job_result = orchestrator.execute("job-pipeline", text="queued")
    check("Job Scheduler Bridge", job_result.ok and job_result.outputs["job-stage"].ok)

    failed = orchestrator.create_pipeline("failed-pipeline")
    orchestrator.add_stage("failed-pipeline", "fail", lambda context, payload, services: (_ for _ in ()).throw(RuntimeError("boom")))
    fail_result = orchestrator.execute("failed-pipeline")
    resume_result = orchestrator.resume("failed-pipeline")
    check("Pipeline Resume", fail_result.status == PipelineStatus.FAILED and resume_result.status == PipelineStatus.FAILED)

    manifest = orchestrator.manifest()
    freeze = validate_freeze_manifest(build_freeze_manifest({"stage": "09.2"}))
    check("Orchestrator Manifest", manifest["stage"] == PIPELINE_ORCHESTRATOR_STAGE and manifest["additive_only"] is True)
    check("Foundation Freeze", freeze.ok and freeze.status == "frozen")
    check("Backward Compatible", manifest["integration_status"] == "frozen" and manifest["workflow_core_compatible"] is True)

    print("PASS")


if __name__ == "__main__":
    main()
