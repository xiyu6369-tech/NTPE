"""Event filters for NTPE Stage-08.5 Event Bus."""
from __future__ import annotations

from typing import Iterable, Optional

from .event_models import Event


class EventFilter:
    def __init__(self, *, topics: Optional[Iterable[str]] = None, types: Optional[Iterable[str]] = None, sources: Optional[Iterable[str]] = None, min_priority: Optional[int] = None) -> None:
        self.topics = set(topics or [])
        self.types = set(types or [])
        self.sources = set(sources or [])
        self.min_priority = min_priority

    def match(self, event: Event) -> bool:
        if self.topics and event.topic not in self.topics:
            return False
        if self.types and event.type not in self.types:
            return False
        if self.sources and event.source not in self.sources:
            return False
        if self.min_priority is not None and event.priority < self.min_priority:
            return False
        return True
