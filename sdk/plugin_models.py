"""Stage-07.7 SDK Plugin API model objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PluginResult:
    plugin_name: str
    status: str = "success"
    output: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status == "success" and self.error is None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_name": self.plugin_name,
            "status": self.status,
            "output": self.output,
            "metadata": dict(self.metadata),
            "error": self.error,
            "ok": self.ok,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginResult":
        return cls(
            plugin_name=str(data.get("plugin_name", "")),
            status=str(data.get("status", "success")),
            output=data.get("output"),
            metadata=dict(data.get("metadata", {})),
            error=data.get("error"),
        )


@dataclass
class PluginDescriptor:
    name: str
    version: str = "1.0.0"
    stage: str = "sdk"
    enabled: bool = True
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "stage": self.stage,
            "enabled": self.enabled,
            "capabilities": list(self.capabilities),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginDescriptor":
        return cls(
            name=str(data.get("name", "")),
            version=str(data.get("version", "1.0.0")),
            stage=str(data.get("stage", "sdk")),
            enabled=bool(data.get("enabled", True)),
            capabilities=list(data.get("capabilities", [])),
            metadata=dict(data.get("metadata", {})),
        )
