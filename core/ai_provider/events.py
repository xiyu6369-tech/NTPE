from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
import time

@dataclass
class ProviderEvent:
    name: str
    provider: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class ProviderEventBus:
    def __init__(self):
        self.history: List[ProviderEvent] = []
    def publish(self, event: ProviderEvent):
        self.history.append(event)
        return event
