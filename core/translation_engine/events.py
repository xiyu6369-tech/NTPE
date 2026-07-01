"""Translation engine event helpers."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time


@dataclass
class TranslationEvent:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    level: str = "info"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "payload": dict(self.payload), "level": self.level, "timestamp": self.timestamp}


class TranslationEventBus:
    """Small in-process event bus with optional bridge to Foundation event bus."""

    def __init__(self, external_bus: Any = None):
        self.external_bus = external_bus
        self.history: List[TranslationEvent] = []
        self.subscribers: Dict[str, List[Any]] = {}

    def subscribe(self, name: str, callback: Any) -> None:
        self.subscribers.setdefault(name, []).append(callback)

    def emit(self, name: str, payload: Optional[Dict[str, Any]] = None, level: str = "info") -> TranslationEvent:
        event = TranslationEvent(name=name, payload=dict(payload or {}), level=level)
        self.history.append(event)
        for callback in self.subscribers.get(name, []):
            callback(event)
        if self.external_bus is not None:
            for method in ("publish", "emit"):
                if hasattr(self.external_bus, method):
                    try:
                        getattr(self.external_bus, method)(event)
                    except TypeError:
                        getattr(self.external_bus, method)(name, event.to_dict())
                    break
        return event

    def manifest(self) -> Dict[str, Any]:
        return {"type": "translation_event_bus", "event_count": len(self.history), "subscribers": {k: len(v) for k, v in self.subscribers.items()}}
