"""Platform service host for NTPE 1.0 Beta Stage-10.0."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .service_manager import PlatformServiceManager


class PlatformServiceHost:
    version = "1.0.0-beta.10.0"
    stage = "10.0"

    def __init__(self, *, event_bus: Any = None, service_container: Any = None, workflow_core: Any = None, job_scheduler: Any = None, pipeline_orchestrator: Any = None, task_queue: Any = None, worker_runtime: Any = None, persistence: Any = None, distributed: Any = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.event_bus = event_bus
        self.service_container = service_container
        self.workflow_core = workflow_core
        self.job_scheduler = job_scheduler
        self.pipeline_orchestrator = pipeline_orchestrator
        self.task_queue = task_queue
        self.worker_runtime = worker_runtime
        self.persistence = persistence
        self.distributed = distributed
        self.metadata = dict(metadata or {})
        self.manager = PlatformServiceManager(event_bus=event_bus, service_container=service_container, metadata=self.metadata)
        self._register_builtin_services()

    def _register_builtin_services(self) -> None:
        builtins = [
            ("event_bus", self.event_bus, []),
            ("service_container", self.service_container, []),
            ("workflow_core", self.workflow_core, ["event_bus", "service_container"]),
            ("job_scheduler", self.job_scheduler, ["workflow_core"]),
            ("pipeline_orchestrator", self.pipeline_orchestrator, ["workflow_core", "job_scheduler"]),
            ("task_queue", self.task_queue, ["pipeline_orchestrator"]),
            ("worker_runtime", self.worker_runtime, ["task_queue"]),
            ("workflow_persistence", self.persistence, ["worker_runtime"]),
            ("distributed_execution", self.distributed, ["workflow_persistence"]),
        ]
        for name, instance, dependencies in builtins:
            if instance is not None:
                self.manager.register_service(name, instance, dependencies=dependencies, metadata={"builtin": True})

    def register_service(self, name: str, instance: Any = None, **kwargs: Any):
        return self.manager.register_service(name, instance, **kwargs)

    def start(self):
        return self.manager.start_all()

    def stop(self):
        return self.manager.stop_all()

    def health(self) -> Dict[str, Any]:
        return self.manager.health()

    def manifest(self) -> Dict[str, Any]:
        manifest = self.manager.manifest()
        manifest.update({
            "version": self.version,
            "stage": self.stage,
            "platform_services": True,
            "builtin_count": self.manager.registry.manifest()["count"],
        })
        return manifest


def create_platform_service_host(**kwargs: Any) -> PlatformServiceHost:
    return PlatformServiceHost(**kwargs)
