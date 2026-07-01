"""Translation orchestrator for NTPE 1.0 Beta Stage-02."""
from __future__ import annotations
from typing import Any, Callable, Dict, Iterable, List, Optional

from .diagnostics import TranslationDiagnostics
from .events import TranslationEventBus
from .manifest import VERSION, build_translation_engine_manifest
from .metrics import TranslationMetrics
from .pipeline import TranslationPipeline
from .recovery import TranslationRecoveryManager
from .session import TranslationSessionManager
from .strategy import TranslationStrategy
from .validator import TranslationValidator

try:  # Optional Stage-01 bridge
    from core.production_runtime import RuntimeHost
except Exception:  # pragma: no cover
    RuntimeHost = None  # type: ignore

try:  # Optional Foundation-08 bridge
    from core.knowledge.runtime.runtime import KnowledgeRuntime
except Exception:  # pragma: no cover
    KnowledgeRuntime = None  # type: ignore


class TranslationOrchestrator:
    version = VERSION

    def __init__(
        self,
        translator: Optional[Callable[[Any, Dict[str, Any]], Any]] = None,
        strategy: Optional[TranslationStrategy] = None,
        production_runtime: Any = None,
        knowledge_runtime: Any = None,
        event_bus: Any = None,
    ):
        self.strategy = strategy or TranslationStrategy()
        self.event_bus = TranslationEventBus(external_bus=event_bus)
        self.metrics = TranslationMetrics()
        self.diagnostics = TranslationDiagnostics()
        self.session = TranslationSessionManager()
        self.recovery = TranslationRecoveryManager(max_retries=self.strategy.max_retries)
        if knowledge_runtime is not None:
            self.knowledge_runtime = knowledge_runtime
        elif KnowledgeRuntime is not None:
            try:
                self.knowledge_runtime = KnowledgeRuntime(event_bus=event_bus)
            except TypeError:
                self.knowledge_runtime = KnowledgeRuntime()
        else:
            self.knowledge_runtime = None
        self.pipeline = TranslationPipeline(translator=translator, knowledge_runtime=self.knowledge_runtime, strategy=self.strategy)
        if production_runtime is not None:
            self.production_runtime = production_runtime
        elif RuntimeHost is not None:
            try:
                self.production_runtime = RuntimeHost(executor=self._runtime_executor, knowledge_runtime=self.knowledge_runtime, event_bus=event_bus)
            except TypeError:
                self.production_runtime = None
        else:
            self.production_runtime = None
        self.validator = TranslationValidator(min_length_ratio=self.strategy.min_length_ratio)

    def translate_segments(self, segments: Iterable[Any], job_id: str = "translation-job", payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        items = list(segments)
        session = self.session.create(job_id=job_id, total_segments=len(items), metadata={"engine_version": self.version})
        self.session.start()
        self.event_bus.emit("TranslationSessionStarted", session.to_dict())
        results: List[Dict[str, Any]] = []
        for index, segment in enumerate(items):
            result = self.process_segment(segment, index=index, payload=payload)
            results.append(result)
            self.session.record(index, result)
        completed = self.session.complete()
        self.event_bus.emit("TranslationSessionCompleted", completed.to_dict())
        return {"type": "translation_engine_result", "version": self.version, "session": completed.to_dict(), "results": results, "manifest": self.manifest()}

    def process_segment(self, segment: Any, index: int = 0, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.metrics.increment("segments_started")
        self.event_bus.emit("TranslationSegmentStarted", {"index": index})
        context = self.pipeline.build_context(segment, index=index, payload=payload)

        def execute() -> Dict[str, Any]:
            return self.pipeline.execute(context)

        result = self.recovery.run(execute)
        validation = self.validator.validate(segment, result, context.to_dict()) if self.strategy.enable_validation else None
        result["validation"] = validation.to_dict() if validation else {"passed": True, "issues": []}
        if not result["validation"].get("passed", True):
            self.diagnostics.record("validation_failed", result["validation"], severity="warning")
            self.event_bus.emit("TranslationValidationFailed", {"index": index, "validation": result["validation"]}, level="warning")
        self.metrics.increment("segments_completed")
        self.metrics.observe("segment_duration_seconds", float(result.get("duration_seconds", 0.0)))
        result["recovery"] = self.recovery.last_result.to_dict()
        self.event_bus.emit("TranslationSegmentCompleted", {"index": index, "passed": result["validation"].get("passed", True)})
        return result

    def _runtime_executor(self, segment: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.process_segment(segment, index=int(payload.get("index", 0)), payload=payload)

    def attach_to_runtime_manifest(self, manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        next_manifest = dict(manifest or {})
        components = list(next_manifest.get("components", []))
        components.append(self.manifest())
        next_manifest["components"] = components
        return next_manifest

    def prompt_package(self, segment: Any, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.pipeline.build_context(segment, payload=payload).prompt_package

    def manifest(self, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        manifest = build_translation_engine_manifest(metadata)
        manifest["components_detail"] = {
            "pipeline": self.pipeline.manifest(),
            "session": self.session.manifest(),
            "strategy": self.strategy.to_dict(),
            "validator": self.validator.manifest(),
            "recovery": self.recovery.manifest(),
            "events": self.event_bus.manifest(),
            "metrics": self.metrics.manifest(),
            "diagnostics": self.diagnostics.manifest(),
        }
        if self.production_runtime is not None and hasattr(self.production_runtime, "manifest"):
            manifest["production_runtime"] = self.production_runtime.manifest()
        return manifest
