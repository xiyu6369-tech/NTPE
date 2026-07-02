"""SDK-CLI bridge models for NTPE Stage-08.2."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

BRIDGE_INTEGRATION_VERSION = "0.8.2"
BRIDGE_INTEGRATION_STAGE = "NTPE 1.0 Beta Stage-08.2 SDK-CLI Bridge"


@dataclass
class BridgeCommand:
    """A normalized command shared by SDK and CLI surfaces."""

    surface: str
    action: str
    payload: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "surface": self.surface,
            "action": self.action,
            "payload": dict(self.payload),
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
        }


@dataclass
class BridgeResult:
    """A stable bridge result object for SDK and CLI callers."""

    ok: bool
    action: str
    surface: str
    value: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, action: str, surface: str, value: Any = None, **metadata: Any) -> "BridgeResult":
        return cls(True, action=action, surface=surface, value=value, metadata=dict(metadata))

    @classmethod
    def failure(cls, action: str, surface: str, error: str, **metadata: Any) -> "BridgeResult":
        return cls(False, action=action, surface=surface, error=error, metadata=dict(metadata))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "action": self.action,
            "surface": self.surface,
            "value": self.value,
            "error": self.error,
            "metadata": dict(self.metadata),
        }


@dataclass
class BridgeEndpoint:
    """Registered SDK/CLI endpoint metadata."""

    name: str
    kind: str
    instance: Any
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "version": self.version,
            "metadata": dict(self.metadata),
        }
