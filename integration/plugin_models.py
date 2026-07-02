"""Plugin integration models for NTPE Stage-08.3."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time

PLUGIN_INTEGRATION_VERSION = "0.8.3"
PLUGIN_INTEGRATION_STAGE = "NTPE 1.0 Beta Stage-08.3 Plugin Integration"


@dataclass
class IntegratedPluginDescriptor:
    name: str
    version: str = "1.0.0"
    source: str = "sdk"
    capabilities: List[str] = field(default_factory=list)
    status: str = "registered"
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: float = field(default_factory=time.time)

    def mark(self, status: str) -> None:
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "source": self.source,
            "capabilities": list(self.capabilities),
            "status": self.status,
            "metadata": dict(self.metadata),
            "registered_at": self.registered_at,
        }


@dataclass
class PluginCommand:
    plugin_name: str
    action: str = "execute"
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "integration"
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_name": self.plugin_name,
            "action": self.action,
            "payload": dict(self.payload),
            "source": self.source,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
        }


@dataclass
class PluginIntegrationResult:
    ok: bool
    plugin_name: str
    action: str
    value: Any = None
    error: Optional[str] = None
    status: str = "completed"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, plugin_name: str, action: str, *, value: Any = None, status: str = "completed", **metadata: Any) -> "PluginIntegrationResult":
        return cls(True, plugin_name=plugin_name, action=action, value=value, status=status, metadata=dict(metadata))

    @classmethod
    def failure(cls, plugin_name: str, action: str, error: str, *, value: Any = None, **metadata: Any) -> "PluginIntegrationResult":
        return cls(False, plugin_name=plugin_name, action=action, value=value, error=str(error), status="failed", metadata=dict(metadata))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "plugin_name": self.plugin_name,
            "action": self.action,
            "value": self.value,
            "error": self.error,
            "status": self.status,
            "metadata": dict(self.metadata),
        }
