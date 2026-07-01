"""NTPE 1.0 Beta Stage-01 Production Runtime host."""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, Iterable, List, Optional

from .checkpoint import RuntimeCheckpointStore
from .manifest import build_production_runtime_manifest
from .metrics import RuntimeMetrics
from .recovery import RuntimeRecoveryManager
from .scheduler import RuntimeScheduler, RuntimeTask
from .session import RuntimeSessionManager
from .telemetry import RuntimeTelemetry

try:  # Optional bridge: Foundation-08.2+
    from core.knowledge.runtime.runtime import KnowledgeRuntime
except Exception:  # pragma: no cover - optional compatibility path
    KnowledgeRuntime = None  # type: ignore


class RuntimeHost:
    """Production runtime facade that orchestrates scheduler, session, recovery and observability."""

    version = "ntpe-1.0-beta-stage-01"

    def __init__(
        self,
        executor: Optional[Callable[[Any, Dict[str, Any]], Any]] = None,
        knowledge_runtime: Any = None,
        event_bus: Any = None,
        checkpoint_dir: str = ".ntpe_runtime_checkpoints",
        max_retries: int = 2,
    ):
        self.event_bus = event_bus
        self.telemetry = RuntimeTelemetry(event_bus=event_bus)
        self.metrics = RuntimeMetrics()
        self.scheduler = RuntimeScheduler()
        self.session = RuntimeSessionManager(RuntimeCheckpointStore(checkpoint_dir))
        self.recovery = RuntimeRecoveryManager(max_retries=max_retries)
        self.executor = executor or self._default_executor
        if knowledge_runtime is not None:
            self.knowledge_runtime = knowledge_runtime
        elif KnowledgeRuntime is not None:
            try:
                self.knowledge_runtime = KnowledgeRuntime(event_bus=event_bus)
            except TypeError:
                self.knowledge_runtime = KnowledgeRuntime()
        else:
            self.knowledge_runtime = None

    def start_session(self, job_id: str = "production-job", session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        session = self.session.create(job_id=job_id, session_id=session_id, metadata=metadata)
        self.session.start()
        self.metrics.increment("sessions_started")
        self.telemetry.emit("ProductionRuntimeSessionStarted", session.to_dict())
        return session.to_dict()

    def submit_job(self, segments: Iterable[Any], job_id: str = "production-job") -> Dict[str, Any]:
        if self.session.current is None:
            self.start_session(job_id=job_id)
        tasks = self.scheduler.submit_many(segments)
        self.metrics.increment("tasks_submitted", len(tasks))
        self.telemetry.emit("ProductionRuntimeJobSubmitted", {"job_id": job_id, "task_count": len(tasks)})
        return {"job_id": job_id, "task_count": len(tasks), "session": self.session.current.to_dict() if self.session.current else None}

    def run_next(self) -> Optional[Dict[str, Any]]:
        task = self.scheduler.next_task()
        if task is None:
            return None
        return self._run_task(task)

    def run_all(self) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        while self.scheduler.pending_count() > 0:
            result = self.run_next()
            if result is not None:
                results.append(result)
        if self.session.current is not None:
            self.session.complete()
            self.telemetry.emit("ProductionRuntimeSessionCompleted", self.session.current.to_dict())
        return {"type": "production_runtime_result", "version": self.version, "results": results, "manifest": self.manifest()}

    def process_segment(self, segment: Any, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        task = self.scheduler.submit(segment=segment, payload=payload)
        return self._run_task(task)

    def resume(self, session_id: str) -> Dict[str, Any]:
        checkpoint = self.session.resume(session_id)
        payload = {"session_id": session_id, "checkpoint": checkpoint.to_dict() if checkpoint else None}
        self.telemetry.emit("ProductionRuntimeResume", payload)
        return payload

    def _run_task(self, task: RuntimeTask) -> Dict[str, Any]:
        started = time.time()
        self.metrics.increment("tasks_started")
        self.telemetry.emit("ProductionRuntimeTaskStarted", {"task_id": task.task_id})

        before_payload: Dict[str, Any] = dict(task.payload or {})
        if self.knowledge_runtime is not None and hasattr(self.knowledge_runtime, "before_segment"):
            before_payload = self.knowledge_runtime.before_segment(segment=task.segment, payload=before_payload)
            self.metrics.increment("knowledge_runtime_before")

        def execute() -> Any:
            return self.executor(task.segment, before_payload)

        try:
            output = self.recovery.run_with_retry(execute)
            if self.knowledge_runtime is not None and hasattr(self.knowledge_runtime, "after_segment"):
                knowledge_after = self.knowledge_runtime.after_segment(segment=task.segment, result={"output": output})
            else:
                knowledge_after = {}
            self.scheduler.complete(task)
            checkpoint = self.session.checkpoint(self.scheduler.completed_count(), {"task_id": task.task_id, "status": "completed"})
            duration = time.time() - started
            self.metrics.increment("tasks_completed")
            self.metrics.observe("task_duration_seconds", duration)
            result = {
                "type": "production_runtime_task_result",
                "version": self.version,
                "task": task.to_dict(),
                "output": output,
                "knowledge": knowledge_after,
                "checkpoint": checkpoint.to_dict(),
                "duration_seconds": duration,
                "recovery": self.recovery.last_result.to_dict(),
            }
            self.telemetry.emit("ProductionRuntimeTaskCompleted", {"task_id": task.task_id, "duration_seconds": duration})
            return result
        except BaseException as exc:  # noqa: BLE001
            if self.session.current is not None:
                self.session.fail(exc)
            self.metrics.increment("tasks_failed")
            self.telemetry.emit("ProductionRuntimeTaskFailed", {"task_id": task.task_id, "error": str(exc)}, level="error")
            raise

    def _default_executor(self, segment: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"segment": segment, "payload": payload, "status": "executed"}

    def manifest(self, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        manifest = build_production_runtime_manifest(metadata)
        manifest["components_detail"] = {
            "scheduler": self.scheduler.manifest(),
            "session": self.session.manifest(),
            "recovery": self.recovery.manifest(),
            "metrics": self.metrics.manifest(),
            "telemetry": self.telemetry.manifest(),
        }
        if self.knowledge_runtime is not None and hasattr(self.knowledge_runtime, "manifest"):
            manifest["knowledge_runtime"] = self.knowledge_runtime.manifest()
        return manifest

    def attach_to_runtime_manifest(self, manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        next_manifest = dict(manifest or {})
        components = list(next_manifest.get("components", []))
        components.append(self.manifest())
        next_manifest["components"] = components
        return next_manifest


__all__ = ["RuntimeHost"]
