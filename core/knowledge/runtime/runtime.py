"""Foundation-08.2 Knowledge Runtime integration facade."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..contracts import KnowledgeItem, KnowledgeQuery
from ..repositories.manager import KnowledgeRepositoryManager
from .context_runtime import KnowledgeContextRuntime
from .manifest import build_knowledge_runtime_manifest
from .prompt_runtime import KnowledgePromptRuntime
from .repository_runtime import KnowledgeRepositoryRuntime
from .session_runtime import KnowledgeSessionRuntime


class KnowledgeRuntime:
    """Coordinate Knowledge Context, Prompt, Repository, and Session runtimes."""

    version = "foundation-08.2"

    def __init__(self, manager: Optional[KnowledgeRepositoryManager] = None, event_bus: Any = None, session_id: str = "default"):
        self.manager = manager or KnowledgeRepositoryManager()
        self.event_bus = event_bus
        self.context = KnowledgeContextRuntime(self.manager)
        self.prompt = KnowledgePromptRuntime(self.context)
        self.repository = KnowledgeRepositoryRuntime(self.manager)
        self.session = KnowledgeSessionRuntime(session_id=session_id, manager=self.manager)

    def _publish(self, name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        if self.event_bus is None:
            return
        event_payload = {"name": name, "version": self.version, **dict(payload or {})}
        if hasattr(self.event_bus, "publish"):
            try:
                self.event_bus.publish(name, event_payload)
            except TypeError:
                self.event_bus.publish(event_payload)

    def before_segment(self, segment: Any = None, payload: Optional[Dict[str, Any]] = None, query: Optional[KnowledgeQuery] = None) -> Dict[str, Any]:
        next_payload = self.repository.before_segment(segment=segment, payload=payload, query=query)
        self._publish("KnowledgeSegmentStarted", {"segment_id": next_payload["knowledge_context"]["segment_id"]})
        return next_payload

    def attach_prompt(self, prompt_package: Optional[Dict[str, Any]] = None, segment: Any = None, query: Optional[KnowledgeQuery] = None) -> Dict[str, Any]:
        package = self.prompt.attach(prompt_package, segment=segment, query=query)
        self._publish("KnowledgePromptAttached", {"component_count": len(package.get("context_components", []))})
        return package

    def after_segment(self, segment: Any = None, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        runtime_result = self.repository.after_segment(segment=segment, result=result)
        checkpoint = self.session.checkpoint("after_segment", {"segment_id": runtime_result["segment_id"]})
        runtime_result["session"] = self.session.build_session_payload()
        runtime_result["checkpoint"] = checkpoint.to_dict()
        self._publish("KnowledgeSegmentCompleted", {"segment_id": runtime_result["segment_id"], "updated_count": runtime_result["updated_count"]})
        return runtime_result

    def process_segment(
        self,
        segment: Any = None,
        payload: Optional[Dict[str, Any]] = None,
        prompt_package: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        query: Optional[KnowledgeQuery] = None,
    ) -> Dict[str, Any]:
        before = self.before_segment(segment=segment, payload=payload, query=query)
        prompt = self.attach_prompt(prompt_package, segment=segment, query=query)
        after = self.after_segment(segment=segment, result=result or {})
        return {
            "type": "knowledge_runtime_payload",
            "version": self.version,
            "before": before,
            "prompt_package": prompt,
            "after": after,
            "manifest": self.manifest(),
        }

    def ingest_value(self, key: str, value: Any, domain: str = "general", source: str = "knowledge_runtime") -> KnowledgeItem:
        item = KnowledgeItem(key=key, value=value, domain=domain, source=source)
        return self.manager.repository.put(item)

    def manifest(self, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        runtime_manifest = build_knowledge_runtime_manifest(metadata)
        runtime_manifest["repository"] = self.manager.repository.manifest().to_dict()
        return runtime_manifest

    def attach_to_runtime_manifest(self, manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        next_manifest = dict(manifest or {})
        components = list(next_manifest.get("components", []))
        components.append(self.manifest())
        next_manifest["components"] = components
        return next_manifest


__all__ = ["KnowledgeRuntime"]
