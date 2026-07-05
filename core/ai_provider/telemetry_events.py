from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

TELEMETRY_REQUEST_STARTED = "telemetry.request.started"
TELEMETRY_REQUEST_COMPLETED = "telemetry.request.completed"
TELEMETRY_REQUEST_FAILED = "telemetry.request.failed"
TELEMETRY_PROVIDER_HEALTH = "telemetry.provider.health"
TELEMETRY_ROUTING_DECISION = "telemetry.routing.decision"
TELEMETRY_EXPORT = "telemetry.export"


@dataclass(frozen=True)
class ProviderTelemetryEvent:
    """Immutable telemetry event emitted by the Stage-14.5 observability layer."""

    event_type: str
    provider: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "provider": self.provider,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "timestamp": self.timestamp,
            "attributes": dict(self.attributes),
        }
