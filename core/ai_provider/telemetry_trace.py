from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def new_trace_id() -> str:
    return uuid.uuid4().hex


def new_span_id() -> str:
    return uuid.uuid4().hex[:16]


@dataclass
class ProviderTraceSpan:
    name: str
    provider: Optional[str] = None
    trace_id: str = field(default_factory=new_trace_id)
    span_id: str = field(default_factory=new_span_id)
    parent_span_id: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: str = "running"

    def finish(self, status: str = "ok", **attributes: Any) -> "ProviderTraceSpan":
        self.ended_at = time.time()
        self.status = status
        self.attributes.update(attributes)
        return self

    @property
    def duration_ms(self) -> float:
        end = self.ended_at if self.ended_at is not None else time.time()
        return max(0.0, (end - self.started_at) * 1000.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "provider": self.provider,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "attributes": dict(self.attributes),
            "status": self.status,
        }


@dataclass
class ProviderTraceRecorder:
    spans: List[ProviderTraceSpan] = field(default_factory=list)

    def start_span(
        self,
        name: str,
        provider: Optional[str] = None,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        **attributes: Any,
    ) -> ProviderTraceSpan:
        span = ProviderTraceSpan(
            name=name,
            provider=provider,
            trace_id=trace_id or new_trace_id(),
            parent_span_id=parent_span_id,
            attributes=dict(attributes),
        )
        self.spans.append(span)
        return span

    def snapshot(self) -> List[dict]:
        return [span.to_dict() for span in self.spans]
