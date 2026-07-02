"""NTPE 1.0 Beta Stage-09.8 Workflow Freeze test."""
from __future__ import annotations

import sys
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration import EventBus, ServiceContainer  # noqa: E402
from workflow import (  # noqa: E402
    WORKFLOW_FREEZE_VERSION,
    WORKFLOW_FREEZE_STATUS,
    build_workflow_freeze_manifest,
    build_workflow_contract,
    build_workflow_compatibility_matrix,
    build_workflow_version_manifest,
    validate_workflow_freeze_manifest,
    write_workflow_freeze_artifacts,
    load_workflow_json,
    workflow_freeze_is_compatible,
    create_distributed_coordinator,
    create_job_scheduler,
    create_pipeline_orchestrator,
    create_task_queue,
    create_worker_runtime,
    create_workflow_core,
    create_workflow_persistence,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("NTPE 1.0 Beta Stage-09.8 Workflow Freeze Test")
    print("=" * 78)

    manifest = build_workflow_freeze_manifest({"stage": "09.8"})
    result = validate_workflow_freeze_manifest(manifest)
    contract = build_workflow_contract()
    matrix = build_workflow_compatibility_matrix()
    version = build_workflow_version_manifest()

    check("Workflow Freeze", result.ok and result.status == WORKFLOW_FREEZE_STATUS)
    check("Workflow Contract", contract["status"] == "frozen" and len(contract["frozen_surfaces"]) >= 7)
    check("Compatibility Matrix", workflow_freeze_is_compatible(matrix))
    check("Version Manifest", version["version"] == WORKFLOW_FREEZE_VERSION and version["status"] == "frozen")

    bus = EventBus()
    container = ServiceContainer(metadata={"stage": "09.8"})
    workflow_core = create_workflow_core(event_bus=bus, service_container=container)
    job_scheduler = create_job_scheduler(event_bus=bus, service_container=container, workflow_core=workflow_core)
    pipeline = create_pipeline_orchestrator(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler)
    task_queue = create_task_queue(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler, pipeline_orchestrator=pipeline)
    worker_runtime = create_worker_runtime(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler, pipeline_orchestrator=pipeline, task_queue=task_queue, worker_count=2)
    persistence = create_workflow_persistence(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler, pipeline_orchestrator=pipeline, task_queue=task_queue, worker_runtime=worker_runtime)
    distributed = create_distributed_coordinator(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler, pipeline_orchestrator=pipeline, task_queue=task_queue, worker_runtime=worker_runtime, persistence=persistence)

    workflow_core.create_workflow("freeze_workflow")
    workflow_core.add_step("freeze_workflow", "prepare", lambda **kw: {"ok": True})
    workflow_result = workflow_core.execute("freeze_workflow")

    job = job_scheduler.schedule_job("freeze_job", lambda **kw: {"job": True})
    pipeline.create_pipeline("freeze_pipeline")
    pipeline.add_stage("freeze_pipeline", "stage_a", lambda **kw: {"stage": True})
    pipeline_result = pipeline.execute("freeze_pipeline")
    task = task_queue.enqueue_task("freeze_task", lambda **kw: {"task": True})
    worker_result = worker_runtime.execute_task(worker_runtime.create_task("freeze_worker_task", lambda **kw: {"worker": True}))
    snapshot = persistence.snapshot_workflow("freeze_snapshot")
    distributed.register_node("freeze-node", capacity=2)
    distributed_task = task_queue.create_task("freeze_distributed", workflow_name="freeze_workflow")
    distributed_result = distributed.distribute_task(distributed_task)

    check("Workflow Compatibility", workflow_result.ok and workflow_core.manifest()["foundation_status"] == "frozen")
    check("Job Scheduler Compatibility", job is not None and job_scheduler.manifest()["foundation_status"] == "frozen")
    check("Pipeline Compatibility", pipeline_result.ok and pipeline.manifest()["integration_status"] == "frozen")
    check("Task Queue Compatibility", task is not None and task_queue.manifest()["foundation_status"] == "frozen")
    check("Worker Compatibility", worker_result.ok and worker_runtime.manifest()["foundation_status"] == "frozen")
    check("Persistence Compatibility", snapshot is not None and persistence.manifest()["foundation_status"] == "frozen")
    check("Distributed Compatibility", distributed_result.ok and distributed.manifest()["nodes"]["node_count"] == 1)

    with tempfile.TemporaryDirectory() as tmp:
        written = write_workflow_freeze_artifacts(tmp, {"stage": "09.8"})
        loaded_manifest = load_workflow_json(written["freeze_manifest.json"])
        loaded_matrix = load_workflow_json(written["compatibility_matrix.json"])
        check("Freeze Artifacts", len(written) == 4 and validate_workflow_freeze_manifest(loaded_manifest).ok)
        check("Artifact Compatibility", workflow_freeze_is_compatible(loaded_matrix))

    check("Runtime Compatibility", manifest["integration_status"] == "frozen")
    check("SDK Compatibility", matrix["matrix"]["sdk_stage_07"] is True)
    check("CLI Compatibility", matrix["matrix"]["cli_freeze"] is True)
    check("Integration Compatibility", matrix["matrix"]["integration_freeze"] is True)
    check("Foundation Freeze", manifest["foundation_status"] == "frozen")
    check("Backward Compatible", manifest["additive_only"] is True and contract["rules"]["backward_compatible"] is True)

    print("PASS")


if __name__ == "__main__":
    main()
