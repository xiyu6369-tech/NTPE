from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from .observability import ProviderObservabilityRuntime


@dataclass
class ProviderRuntimeTelemetry:
    """Stable named entry point for Runtime/Web UI telemetry consumers."""

    observability: ProviderObservabilityRuntime = field(default_factory=ProviderObservabilityRuntime)

    def snapshot(self) -> Dict[str, object]:
        return self.observability.snapshot()

    def manifest(self) -> Dict[str, object]:
        return {
            "component": "provider_runtime_telemetry",
            "stage": "NTPE 1.2 Professional Stage-14.5",
            "observability": self.observability.manifest(),
        }
