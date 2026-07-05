from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from .plugin_manager import OFFICIAL_PLUGIN_KINDS, TranslationPluginManager


PIPELINE_PLUGIN_MAP: dict[str, str] = {
    "Encoding": "context",
    "Chunk": "context",
    "Context": "context",
    "Glossary": "glossary",
    "Character Memory": "character_memory",
    "Prompt Builder": "prompt",
    "AI Provider": "provider",
    "QA": "qa",
    "Taiwan Formatter": "formatter",
    "Output": "output",
}


@dataclass(frozen=True)
class PluginRuntimeEvent:
    """Serializable plugin runtime event used by Pipeline/Runtime diagnostics."""

    event_id: str
    stage: str
    plugin_kind: str
    plugin_name: str
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "stage": self.stage,
            "plugin_kind": self.plugin_kind,
            "plugin_name": self.plugin_name,
            "status": self.status,
            "metadata": dict(self.metadata),
        }


class TranslationPluginRuntime:
    """Stage-09 runtime bridge between Pipeline steps and TranslationPluginManager.

    The bridge is intentionally additive. It does not replace Stage-08 plugin
    registration or Stage-06 pipeline handlers; it provides a deterministic
    adapter that lets every official pipeline step execute the matching plugin
    kind with the same payload contract.
    """

    version = "1.2-professional-stage-09"
    compatibility_floor = "1.1-lts-stable"

    def __init__(self, root: str | Path, manager: TranslationPluginManager | None = None):
        self.root = Path(root)
        self.manager = manager or TranslationPluginManager(self.root)
        self.events: list[PluginRuntimeEvent] = []

    def map_step(self, step_name: str) -> str:
        return PIPELINE_PLUGIN_MAP.get(step_name, step_name.lower().replace(" ", "_"))

    def execute_step_plugin(
        self,
        step_name: str,
        payload: dict[str, Any] | None = None,
        plugin_name: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        plugin_kind = self.map_step(step_name)
        meta = dict(metadata or {})
        meta.update({"pipeline_step": step_name, "plugin_runtime_version": self.version})
        result = self.manager.execute(plugin_kind, name=plugin_name, payload=dict(payload or {}), metadata=meta)
        event = PluginRuntimeEvent(
            event_id=uuid4().hex,
            stage=step_name,
            plugin_kind=plugin_kind,
            plugin_name=plugin_name,
            status=result.get("status", "unknown"),
            metadata={"error": result.get("error"), "payload_keys": sorted(result.get("payload", {}).keys())},
        )
        self.events.append(event)
        return {**result, "plugin_kind": plugin_kind, "pipeline_step": step_name, "event": event.to_dict()}

    def build_pipeline_handlers(self) -> dict[str, Any]:
        """Return handlers compatible with TranslationPipelineManager.execute."""

        def _handler(context: dict[str, Any]) -> dict[str, Any]:
            step = context.get("step", {})
            step_name = step.get("name") or "unknown"
            payload = dict(context.get("payload", {}))
            result = self.execute_step_plugin(step_name, payload=payload, metadata={"state": context.get("state", {})})
            if result.get("status") == "failed":
                raise RuntimeError(result.get("error") or f"plugin failed: {step_name}")
            output_payload = dict(result.get("payload", {}))
            trace = list(output_payload.get("plugin_runtime_trace", []))
            trace.append({"step": step_name, "kind": result.get("plugin_kind"), "status": result.get("status")})
            output_payload["plugin_runtime_trace"] = trace
            return {"payload": output_payload, "plugin_result": result}

        return {
            "encoding": _handler,
            "chunk": _handler,
            "context": _handler,
            "glossary": _handler,
            "character_memory": _handler,
            "prompt_builder": _handler,
            "ai_provider": _handler,
            "qa": _handler,
            "taiwan_formatter": _handler,
            "output": _handler,
        }

    def execute_pipeline(self, pipeline: Any, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return pipeline.execute(payload=payload, handlers=self.build_pipeline_handlers())

    def validate(self) -> dict[str, Any]:
        manager_status = self.manager.validate()
        missing = [kind for kind in set(PIPELINE_PLUGIN_MAP.values()) if self.manager.registry.get(kind, "default") is None]
        unsupported = [kind for kind in PIPELINE_PLUGIN_MAP.values() if kind not in OFFICIAL_PLUGIN_KINDS]
        status = "success" if manager_status.get("status") == "success" and not missing and not unsupported else "failed"
        return {
            "status": status,
            "version": self.version,
            "compatibility_floor": self.compatibility_floor,
            "pipeline_plugin_map": dict(PIPELINE_PLUGIN_MAP),
            "missing": sorted(missing),
            "unsupported": sorted(set(unsupported)),
            "manager": manager_status,
        }

    def describe(self) -> dict[str, Any]:
        return {
            "status": "success",
            "version": self.version,
            "compatibility_floor": self.compatibility_floor,
            "pipeline_plugin_map": dict(PIPELINE_PLUGIN_MAP),
            "event_count": len(self.events),
            "events": [event.to_dict() for event in self.events],
        }
