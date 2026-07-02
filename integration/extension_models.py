"""Extension framework models for NTPE Stage-08.4."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time

EXTENSION_FRAMEWORK_VERSION = "0.8.4"
EXTENSION_FRAMEWORK_STAGE = "NTPE 1.0 Beta Stage-08.4 Extension Framework"


@dataclass
class ExtensionManifest:
    name: str
    version: str = "1.0.0"
    entrypoint: str = ""
    capabilities: List[str] = field(default_factory=list)
    kind: str = "extension"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        if not self.name or not isinstance(self.name, str):
            raise ValueError("extension manifest requires name")
        if not self.version or not isinstance(self.version, str):
            raise ValueError("extension manifest requires version")
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "entrypoint": self.entrypoint,
            "capabilities": list(self.capabilities),
            "kind": self.kind,
            "metadata": dict(self.metadata),
        }


@dataclass
class ExtensionDescriptor:
    manifest: ExtensionManifest
    source: str = "integration"
    status: str = "registered"
    enabled: bool = False
    registered_at: float = field(default_factory=time.time)

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def capabilities(self) -> List[str]:
        return list(self.manifest.capabilities)

    def mark(self, status: str) -> None:
        self.status = status
        if status == "enabled":
            self.enabled = True
        elif status in {"disabled", "unloaded"}:
            self.enabled = False

    def to_dict(self) -> Dict[str, Any]:
        data = self.manifest.to_dict()
        data.update({"source": self.source, "status": self.status, "enabled": self.enabled, "registered_at": self.registered_at})
        return data


@dataclass
class ExtensionCommand:
    extension_name: str
    action: str = "execute"
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "integration"
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extension_name": self.extension_name,
            "action": self.action,
            "payload": dict(self.payload),
            "source": self.source,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
        }


@dataclass
class ExtensionResult:
    ok: bool
    extension_name: str
    action: str
    value: Any = None
    error: Optional[str] = None
    status: str = "completed"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, extension_name: str, action: str, *, value: Any = None, status: str = "completed", **metadata: Any) -> "ExtensionResult":
        return cls(True, extension_name=extension_name, action=action, value=value, status=status, metadata=dict(metadata))

    @classmethod
    def failure(cls, extension_name: str, action: str, error: str, *, value: Any = None, **metadata: Any) -> "ExtensionResult":
        return cls(False, extension_name=extension_name, action=action, value=value, error=str(error), status="failed", metadata=dict(metadata))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "extension_name": self.extension_name,
            "action": self.action,
            "value": self.value,
            "error": self.error,
            "status": self.status,
            "metadata": dict(self.metadata),
        }
