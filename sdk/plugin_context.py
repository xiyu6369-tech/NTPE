"""Stage-07.7 SDK Plugin execution context."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class SDKPluginContext:
    runtime: Any = None
    config: Any = None
    session: Any = None
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    callback: Optional[Callable[[Dict[str, Any]], None]] = None

    def emit(self, event_type: str, **data: Any) -> Dict[str, Any]:
        event = {"type": event_type, "data": dict(data), "metadata": dict(self.metadata)}
        self.events.append(event)
        if self.callback:
            self.callback(event)
        return event

    def child(self, **updates: Any) -> "SDKPluginContext":
        payload = dict(self.payload)
        metadata = dict(self.metadata)
        payload.update(updates.pop("payload", {}))
        metadata.update(updates.pop("metadata", {}))
        return SDKPluginContext(
            runtime=updates.pop("runtime", self.runtime),
            config=updates.pop("config", self.config),
            session=updates.pop("session", self.session),
            payload=payload,
            metadata=metadata,
            callback=updates.pop("callback", self.callback),
        )

    def to_runtime_bridge(self) -> Dict[str, Any]:
        return {
            "runtime_attached": self.runtime is not None,
            "config_attached": self.config is not None,
            "session_attached": self.session is not None,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
            "events": list(self.events),
        }
