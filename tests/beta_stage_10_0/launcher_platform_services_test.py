"""NTPE 1.0 Beta Stage-10.0 Platform Services test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
from platform_services import (  # noqa: E402
    PLATFORM_SERVICES_STAGE,
    PlatformServiceManager,
    PlatformServiceStatus,
    create_platform_service_host,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class DemoService:
    def __init__(self) -> None:
        self.started = False

    def start(self):
        self.started = True
        return {"demo": "started"}

    def stop(self):
        self.started = False
        return {"demo": "stopped"}


def main() -> None:
    print("NTPE 1.0 Beta Stage-10.0 Platform Services Test")
    print("=" * 78)

    bus = EventBus()
    container = ServiceContainer(metadata={"stage": "10.0"})
    workflow_core = create_workflow_core(event_bus=bus, service_container=container)
    job_scheduler = create_job_scheduler(event_bus=bus, service_container=container, workflow_core=workflow_core)
    pipeline = create_pipeline_orchestrator(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler)
    task_queue = create_task_queue(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler, pipeline_orchestrator=pipeline)
    worker_runtime = create_worker_runtime(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler, pipeline_orchestrator=pipeline, task_queue=task_queue, worker_count=2)
    persistence = create_workflow_persistence(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler, pipeline_orchestrator=pipeline, task_queue=task_queue, worker_runtime=worker_runtime)
    distributed = create_distributed_coordinator(event_bus=bus, service_container=container, workflow_core=workflow_core, job_scheduler=job_scheduler, pipeline_orchestrator=pipeline, task_queue=task_queue, worker_runtime=worker_runtime, persistence=persistence)

    host = create_platform_service_host(
        event_bus=bus,
        service_container=container,
        workflow_core=workflow_core,
        job_scheduler=job_scheduler,
        pipeline_orchestrator=pipeline,
        task_queue=task_queue,
        worker_runtime=worker_runtime,
        persistence=persistence,
        distributed=distributed,
        metadata={"stage": "10.0"},
    )

    manifest = host.manifest()
    check("Platform Stage", PLATFORM_SERVICES_STAGE == "10.0" and manifest["stage"] == "10.0")
    check("Builtin Services", manifest["builtin_count"] >= 9)
    check("Foundation Compatible", manifest["foundation_status"] == "frozen")
    check("CLI Compatible", manifest["cli_status"] == "frozen")
    check("SDK Compatible", manifest["sdk_status"] == "complete")
    check("Integration Compatible", manifest["integration_status"] == "frozen")
    check("Workflow Compatible", manifest["workflow_status"] == "frozen")
    check("Additive Only", manifest["additive_only"] is True)

    demo = DemoService()
    descriptor = host.register_service("demo_service", demo, dependencies=["workflow_core"], metadata={"custom": True})
    check("Custom Registered", descriptor.name == "demo_service" and descriptor.status == PlatformServiceStatus.REGISTERED)
    start_results = host.start()
    check("Services Started", all(result.ok for result in start_results) and demo.started is True)
    check("Container Bridge", container.try_resolve("demo_service").ok)
    health = host.health()
    check("Health Report", health["ok"] is True and health["count"] >= 10)
    stop_results = host.stop()
    check("Services Stopped", all(result.ok for result in stop_results) and demo.started is False)
    check("Event Bridge", len(bus.history) >= 3)

    manager = PlatformServiceManager(event_bus=bus, service_container=container)
    manager.register_service("alpha", object())
    manager.register_service("beta", object(), dependencies=["alpha"])
    ordered = [result.service for result in manager.start_all()]
    check("Dependency Order", ordered == ["alpha", "beta"])
    check("Manager Manifest", manager.manifest()["registry"]["count"] == 2)

    print("PASS")


if __name__ == "__main__":
    main()
