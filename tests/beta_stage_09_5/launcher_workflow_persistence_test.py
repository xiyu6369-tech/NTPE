"""NTPE 1.0 Beta Stage-09.5 Workflow Persistence test."""
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
    WorkerRuntime,
    WorkflowPersistence,
    PersistenceStore,
    PersistenceStatus,
    SnapshotKind,
    WORKFLOW_PERSISTENCE_STAGE,
)
from integration import EventBus, ServiceContainer, build_freeze_manifest, validate_freeze_manifest  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<36} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("NTPE 1.0 Beta Stage-09.5 Workflow Persistence Test")
    print("=" * 76)

    bus = EventBus()
    container = ServiceContainer(metadata={"stage": "09.5"})
    container.register_instance("prefix", "persisted")

    workflow_core = WorkflowCore(event_bus=bus, service_container=container, metadata={"stage": "09.5"})
    workflow = workflow_core.create_workflow("persistence-workflow")
    workflow.add_step("load", lambda context, payload, services: payload.get("text", ""))
    workflow.add_step("translate", lambda context, payload, services: f"{services.resolve('prefix')}:{context.get('load')}", depends_on=["load"])

    scheduler = JobScheduler(event_bus=bus, service_container=container, workflow_core=workflow_core, metadata={"stage": "09.5"})
    orchestrator = PipelineOrchestrator(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=scheduler, metadata={"stage": "09.5"})
    pipeline = orchestrator.create_pipeline("persistence-pipeline")
    orchestrator.add_stage("persistence-pipeline", "normalize", lambda context, payload, services: payload.get("text", "").strip())

    queue = WorkflowTaskQueue(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=scheduler, pipeline_orchestrator=orchestrator, metadata={"stage": "09.5"})
    runtime = WorkerRuntime(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=scheduler, pipeline_orchestrator=orchestrator, task_queue=queue, worker_count=1, metadata={"stage": "09.5"})
    runtime.start()

    task = queue.enqueue_task("persist-task", workflow_name="persistence-workflow", payload={"text": "chapter"})
    result = runtime.run_next()
    check("Worker Integration", result.ok and result.output.outputs["translate"] == "persisted:chapter")

    persistence = WorkflowPersistence(
        event_bus=bus,
        service_container=container,
        workflow_core=workflow_core,
        job_scheduler=scheduler,
        pipeline_orchestrator=orchestrator,
        task_queue=queue,
        worker_runtime=runtime,
        store=PersistenceStore(),
        metadata={"stage": "09.5"},
    )

    state = {
        "workflow": workflow.name,
        "pipeline_id": pipeline.pipeline_id,
        "task_id": task.task_id,
        "result": result.to_dict(),
    }
    snapshot_result = persistence.snapshot_workflow("translation-run", state=state, source="test")
    check("Workflow Persistence", snapshot_result.ok and snapshot_result.status == PersistenceStatus.SAVED)
    check("Workflow Snapshot", snapshot_result.snapshot.kind == SnapshotKind.WORKFLOW)

    checkpoint_result = persistence.checkpoint("after-task", snapshot=snapshot_result.snapshot, task_id=task.task_id)
    check("Checkpoint Created", checkpoint_result.ok and checkpoint_result.checkpoint.snapshot_id == snapshot_result.snapshot.snapshot_id)

    loaded = persistence.load(snapshot_result.snapshot.snapshot_id)
    check("Persistence Deserialization", loaded.state["result"]["ok"] is True)
    check("Persistence Serialization", loaded.metadata["source"] == "test")

    class Target:
        metadata = {}
        recovered_state = {}

    target = Target()
    recovery_result = persistence.resume(snapshot_result.snapshot.snapshot_id, target=target)
    check("Workflow Resume", recovery_result.ok and recovery_result.status == PersistenceStatus.RECOVERED)
    check("Recovery Manager", target.recovered_state["workflow"] == "persistence-workflow")

    manifest = persistence.manifest()
    freeze = validate_freeze_manifest(build_freeze_manifest({"stage": "09.5"}))
    check("Runtime Integration", manifest["bridges"]["worker_runtime_attached"] is True)
    check("Event Bus Integration", len([e for e in bus.history if "persistence" in e.get("event", {}).get("type", "")]) >= 5)
    check("Worker Runtime Compatible", manifest["worker_runtime_compatible"] is True)
    check("Foundation Freeze", freeze.ok and freeze.status == "frozen")
    check("Backward Compatible", manifest["integration_status"] == "frozen" and manifest["additive_only"] is True)
    check("Stage Marker", manifest["stage"] == WORKFLOW_PERSISTENCE_STAGE)

    print("PASS")


if __name__ == "__main__":
    main()
