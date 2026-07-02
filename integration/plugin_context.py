"""Shared plugin context for integration-managed plugins."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class PluginIntegrationContext:
    operation: str
    plugin_name: Optional[str] = None
    runtime: Any = None
    sdk: Any = None
    cli: Any = None
    config: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: str = field(default_factory=lambda: f"plugin-{uuid4().hex[:12]}")

    def child(self, operation: str, **metadata: Any) -> "PluginIntegrationContext":
        merged = dict(self.metadata)
        merged.update(metadata)
        merged["parent_correlation_id"] = self.correlation_id
        return PluginIntegrationContext(
            operation=operation,
            plugin_name=self.plugin_name,
            runtime=self.runtime,
            sdk=self.sdk,
            cli=self.cli,
            config=dict(self.config),
            session_id=self.session_id,
            metadata=merged,
        )

    def to_sdk_context(self) -> Any:
        try:
            from sdk import SDKPluginContext
            return SDKPluginContext(runtime=self.runtime, config=dict(self.config), session=self.session_id, payload={}, metadata=dict(self.metadata))
        except Exception:
            return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "plugin_name": self.plugin_name,
            "runtime_attached": self.runtime is not None,
            "sdk_attached": self.sdk is not None,
            "cli_attached": self.cli is not None,
            "config": dict(self.config),
            "session_id": self.session_id,
            "metadata": dict(self.metadata),
            "correlation_id": self.correlation_id,
        }
