from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


@dataclass(frozen=True)
class PluginContext:
    """Immutable metadata passed to NTPE translation plugins."""

    stage: str
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_payload(self, payload: dict[str, Any]) -> "PluginContext":
        return PluginContext(stage=self.stage, payload=dict(payload), metadata=dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {"stage": self.stage, "payload": dict(self.payload), "metadata": dict(self.metadata)}


@dataclass(frozen=True)
class PluginResult:
    """Stable plugin execution result contract."""

    status: str = "success"
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
            "error": self.error,
        }


class TranslationPluginProtocol(Protocol):
    name: str
    kind: str
    version: str
    enabled: bool

    def execute(self, context: PluginContext) -> PluginResult | dict[str, Any]:
        ...


PluginCallable = Callable[[PluginContext], PluginResult | dict[str, Any]]


@dataclass
class TranslationPlugin:
    """Default concrete plugin implementation.

    Stage-08 keeps plugins metadata-first and additive.  A plugin may wrap a
    callable, but disabled plugins are skipped by the manager and never mutate
    Foundation/LTS files.
    """

    name: str
    kind: str
    handler: PluginCallable | None = None
    version: str = "1.2-professional-stage-08"
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def execute(self, context: PluginContext) -> PluginResult:
        if not self.enabled:
            return PluginResult(status="skipped", payload=dict(context.payload), metadata={"plugin": self.name, "reason": "disabled"})
        if self.handler is None:
            trace = list(context.payload.get("plugin_trace", []))
            trace.append(self.name)
            payload = dict(context.payload)
            payload["plugin_trace"] = trace
            return PluginResult(status="success", payload=payload, metadata={"plugin": self.name, "kind": self.kind})
        result = self.handler(context)
        if isinstance(result, PluginResult):
            return result
        if not isinstance(result, dict):
            return PluginResult(status="success", payload={"value": result}, metadata={"plugin": self.name})
        status = result.get("status", "success")
        payload = result.get("payload", result)
        metadata = result.get("metadata", {})
        error = result.get("error")
        return PluginResult(status=status, payload=dict(payload), metadata=dict(metadata), error=error)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "version": self.version,
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }
