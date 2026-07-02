"""Shared extension context for NTPE Stage-08.4."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class ExtensionContext:
    operation: str
    extension_name: Optional[str] = None
    runtime: Any = None
    sdk: Any = None
    cli: Any = None
    plugin_manager: Any = None
    config: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: str = field(default_factory=lambda: f"extension-{uuid4().hex[:12]}")

    def child(self, operation: str, **metadata: Any) -> "ExtensionContext":
        merged = dict(self.metadata)
        merged.update(metadata)
        merged["parent_correlation_id"] = self.correlation_id
        return ExtensionContext(
            operation=operation,
            extension_name=self.extension_name,
            runtime=self.runtime,
            sdk=self.sdk,
            cli=self.cli,
            plugin_manager=self.plugin_manager,
            config=dict(self.config),
            session_id=self.session_id,
            metadata=merged,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "extension_name": self.extension_name,
            "runtime_attached": self.runtime is not None,
            "sdk_attached": self.sdk is not None,
            "cli_attached": self.cli is not None,
            "plugin_manager_attached": self.plugin_manager is not None,
            "config": dict(self.config),
            "session_id": self.session_id,
            "metadata": dict(self.metadata),
            "correlation_id": self.correlation_id,
        }
