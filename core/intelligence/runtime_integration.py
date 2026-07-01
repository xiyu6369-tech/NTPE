"""Foundation-07.2 Intelligence Runtime Integration.

This module connects the Foundation-07.1 TranslationIntelligenceEngine to runtime
execution without requiring changes to existing Runtime classes. It is intentionally
adapter-based and dict-friendly so legacy Runtime/Prompt callers remain compatible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple

from .engine import TranslationIntelligenceEngine
from .memory_store import IntelligenceMemoryStore


@dataclass
class RuntimeIntelligencePacket:
    """Serializable packet exchanged between Runtime and Intelligence layers."""

    segment_id: Optional[str]
    source_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    prompt_package: Dict[str, Any] = field(default_factory=dict)
    runtime_manifest: Dict[str, Any] = field(default_factory=dict)
    prompt_context: Dict[str, Any] = field(default_factory=dict)
    snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "source_text": self.source_text,
            "metadata": dict(self.metadata),
            "prompt_package": dict(self.prompt_package),
            "runtime_manifest": dict(self.runtime_manifest),
            "prompt_context": dict(self.prompt_context),
            "snapshot": dict(self.snapshot),
        }


class TranslationIntelligenceRuntimeIntegration:
    """Runtime-safe integration facade for Translation Intelligence.

    The integration layer never imports a concrete Runtime implementation. Existing
    callers can use it in three modes:

    1. before_segment(...): attach intelligence prompt context and manifest data.
    2. after_segment(...): validate translated output and return updated snapshot.
    3. wrap_executor(...): wrap any callable executor with pre/post intelligence hooks.
    """

    version = "foundation-07.2"

    def __init__(
        self,
        engine: Optional[TranslationIntelligenceEngine] = None,
        store: Optional[IntelligenceMemoryStore] = None,
    ) -> None:
        self.engine = engine or TranslationIntelligenceEngine(store=store)

    def before_segment(
        self,
        segment: Any,
        prompt_package: Optional[Dict[str, Any]] = None,
        runtime_manifest: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RuntimeIntelligencePacket:
        """Build the prompt/runtime intelligence packet before execution."""

        segment_id, source_text, segment_metadata = self._extract_segment(segment)
        merged_metadata = dict(segment_metadata)
        merged_metadata.update(dict(metadata or {}))

        next_prompt_package = self.engine.attach_to_prompt_package(
            prompt_package or {},
            source_text=source_text,
        )
        next_runtime_manifest = self.engine.attach_to_manifest(runtime_manifest or {})
        prompt_context = self.engine.build_prompt_context(source_text=source_text)
        snapshot = self.engine.build_snapshot()

        manifest = dict(snapshot.get("manifest", {}))
        manifest.update(
            {
                "component": "translation_intelligence_runtime_integration",
                "foundation": "07.2",
                "integration_version": self.version,
            }
        )
        snapshot["manifest"] = manifest

        next_runtime_manifest = self._append_unique_component(
            next_runtime_manifest,
            {
                "name": "translation_intelligence_runtime_integration",
                "version": self.version,
                "enabled": True,
                "manifest": manifest,
            },
        )

        return RuntimeIntelligencePacket(
            segment_id=segment_id,
            source_text=source_text,
            metadata=merged_metadata,
            prompt_package=next_prompt_package,
            runtime_manifest=next_runtime_manifest,
            prompt_context=prompt_context,
            snapshot=snapshot,
        )

    def after_segment(
        self,
        segment: Any,
        output_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validate translated output and expose updated runtime intelligence state."""

        segment_id, source_text, segment_metadata = self._extract_segment(segment)
        merged_metadata = dict(segment_metadata)
        merged_metadata.update(dict(metadata or {}))

        processed = self.engine.process_segment(
            source_text=source_text,
            output_text=output_text,
            segment_id=segment_id,
            metadata=merged_metadata,
        )
        snapshot = dict(processed.get("snapshot", {}))
        manifest = dict(snapshot.get("manifest", {}))
        manifest.update(
            {
                "component": "translation_intelligence_runtime_integration",
                "foundation": "07.2",
                "integration_version": self.version,
                "last_segment_id": segment_id,
            }
        )
        snapshot["manifest"] = manifest
        processed["snapshot"] = snapshot
        processed["runtime_integration"] = {
            "version": self.version,
            "stage": "after_segment",
            "segment_id": segment_id,
        }
        return processed

    def process_runtime_segment(
        self,
        segment: Any,
        output_text: str = "",
        prompt_package: Optional[Dict[str, Any]] = None,
        runtime_manifest: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run the complete intelligence integration cycle for one segment."""

        before = self.before_segment(
            segment=segment,
            prompt_package=prompt_package,
            runtime_manifest=runtime_manifest,
            metadata=metadata,
        )
        result: Dict[str, Any] = {
            "segment_id": before.segment_id,
            "before": before.to_dict(),
            "prompt_package": before.prompt_package,
            "runtime_manifest": before.runtime_manifest,
            "snapshot": before.snapshot,
        }
        if output_text:
            result["after"] = self.after_segment(segment, output_text=output_text, metadata=metadata)
            result["consistency"] = result["after"].get("consistency", {})
            result["snapshot"] = result["after"].get("snapshot", before.snapshot)
        return result

    def attach_to_runtime_payload(
        self,
        payload: Optional[Dict[str, Any]],
        segment: Any,
    ) -> Dict[str, Any]:
        """Attach intelligence data to a generic Runtime payload dict."""

        next_payload: Dict[str, Any] = dict(payload or {})
        packet = self.before_segment(
            segment=segment,
            prompt_package=next_payload.get("prompt_package", {}),
            runtime_manifest=next_payload.get("runtime_manifest", {}),
            metadata=next_payload.get("metadata", {}),
        )
        next_payload["prompt_package"] = packet.prompt_package
        next_payload["runtime_manifest"] = packet.runtime_manifest
        next_payload["intelligence"] = {
            "version": self.version,
            "prompt_context": packet.prompt_context,
            "snapshot": packet.snapshot,
        }
        return next_payload

    def wrap_executor(self, executor: Callable[..., str]) -> Callable[..., Dict[str, Any]]:
        """Wrap a string-returning executor with intelligence pre/post hooks."""

        def wrapped(segment: Any, *args: Any, **kwargs: Any) -> Dict[str, Any]:
            before = self.before_segment(segment)
            output_text = executor(segment, *args, **kwargs)
            after = self.after_segment(segment, output_text=output_text)
            return {
                "output_text": output_text,
                "before": before.to_dict(),
                "after": after,
                "consistency": after.get("consistency", {}),
            }

        return wrapped

    def _extract_segment(self, segment: Any) -> Tuple[Optional[str], str, Dict[str, Any]]:
        """Extract segment id/text/metadata from dicts or simple runtime objects."""

        if isinstance(segment, dict):
            segment_id = segment.get("segment_id") or segment.get("id")
            source_text = str(
                segment.get("source_text")
                or segment.get("text")
                or segment.get("content")
                or ""
            )
            metadata = dict(segment.get("metadata") or {})
            return segment_id, source_text, metadata

        segment_id = getattr(segment, "segment_id", None) or getattr(segment, "id", None)
        source_text = str(
            getattr(segment, "source_text", "")
            or getattr(segment, "text", "")
            or getattr(segment, "content", "")
            or ""
        )
        metadata_value = getattr(segment, "metadata", {}) or {}
        metadata = dict(metadata_value) if isinstance(metadata_value, dict) else {"metadata": metadata_value}
        return segment_id, source_text, metadata

    def _append_unique_component(self, manifest: Dict[str, Any], component: Dict[str, Any]) -> Dict[str, Any]:
        next_manifest = dict(manifest or {})
        components = list(next_manifest.get("components", []))
        name = component.get("name")
        version = component.get("version")
        if not any(item.get("name") == name and item.get("version") == version for item in components if isinstance(item, dict)):
            components.append(component)
        next_manifest["components"] = components
        return next_manifest
