"""NTPE 1.0 Beta Stage-09.6 Distributed Execution test."""
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
    DistributedCoordinator,
    DistributionStrategy,
    NodeStatus,
    DISTRIBUTED_EXECUTION_STAGE,
)
from integration import EventBus, ServiceContainer, build_freeze_manifest, validate_freeze_manifest  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<36} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("NTPE 1.0 Beta Stage-09.6 Distributed Execution Test")
    print("=" * 78)

    bus = EventBus()
    container = ServiceContainer(metadata={"stage": "09.6"})
    container.register_instance("prefix", "distributed")

    workflow_core = WorkflowCore(event_bus=bus, service_container=container, metadata={"stage": "09.6"})
    workflow = workflow_core.create_workflow("distributed-workflow")
    workflow.add_step("load", lambda context, payload, services: payload.get("text", ""))
    workflow.add_step("translate", lambda context, payload, services: f"{services.resolve('prefix')}:{context.get('load')}", depends_on=["load"])

    scheduler = JobScheduler(event_bus=bus, service_container=container, workflow_core=workflow_core, metadata={"stage": "09.6"})
    orchestrator = PipelineOrchestrator(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=scheduler, metadata={"stage": "09.6"})
    queue = WorkflowTaskQueue(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=scheduler, pipeline_orchestrator=orchestrator, metadata={"stage": "09.6"})
    runtime = WorkerRuntime(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=scheduler, pipeline_orchestrator=orchestrator, task_queue=queue, worker_count=1, metadata={"stage": "09.6"})
    runtime.start()
    persistence = WorkflowPersistence(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=scheduler, pipeline_orchestrator=orchestrator, task_queue=queue, worker_runtime=runtime, store=PersistenceStore(), metadata={"stage": "09.6"})

    coordinator = DistributedCoordinator(
        event_bus=bus,
        service_container=container,
        workflow_core=workflow_core,
        job_scheduler=scheduler,
        pipeline_orchestrator=orchestrator,
        task_queue=queue,
        worker_runtime=runtime,
        persistence=persistence,
        strategy=DistributionStrategy.LEAST_LOADED,
        metadata={"stage": "09.6"},
    ).start()

    node_a = coordinator.register_node("node-a", capacity=2, region="local")
    node_b = coordinator.register_node("node-b", capacity=1, region="local")
    check("Distributed Coordinator", coordinator.running is True)
    check("Node Registry", len(coordinator.registry.online()) == 2)

    task = queue.create_task("distributed-task", workflow_name="distributed-workflow", payload={"text": "chapter"})
    result = coordinator.distribute_task(task)
    check("Task Distribution", result.ok and result.node_id in {node_a.node_id, node_b.node_id})
    check("Runtime Integration", result.output.ok is True)
    check("Workflow Integration", result.output.output.outputs["translate"] == "distributed:chapter")

    coordinator.beat(node_a.node_id)
    check("Heartbeat", coordinator.registry.get(node_a.node_id).last_heartbeat is not None)

    # Force the first node to fail, then ensure the task is redistributed to another node.
    failover_task = queue.create_task("failover-task", workflow_name="distributed-workflow", payload={"text": "retry"})
    failover_result = coordinator.failover(node_a.node_id, failover_task)
    check("Failover", failover_result.ok and coordinator.registry.get(node_a.node_id).status == NodeStatus.FAILED)
    check("Load Balancing", failover_result.node_id == node_b.node_id)

    manifest = coordinator.manifest()
    freeze = validate_freeze_manifest(build_freeze_manifest({"stage": "09.6"}))
    distributed_events = [e for e in bus.history if "distributed" in e.get("event", {}).get("type", "")]
    check("Distributed Event Dispatch", len(distributed_events) >= 6)
    check("Persistence Integration", manifest["bridges"]["persistence_attached"] is True)
    check("Worker Runtime Compatible", manifest["worker_runtime_compatible"] is True)
    check("Foundation Freeze", freeze.ok and freeze.status == "frozen")
    check("Backward Compatible", manifest["integration_status"] == "frozen" and manifest["additive_only"] is True)
    check("Stage Marker", manifest["stage"] == DISTRIBUTED_EXECUTION_STAGE)

    print("PASS")


if __name__ == "__main__":
    main()
