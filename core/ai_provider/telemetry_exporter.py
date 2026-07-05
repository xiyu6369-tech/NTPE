from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping


@dataclass
class ProviderTelemetryExporter:
    """Exports telemetry snapshots without introducing external dependencies."""

    def export_json(self, snapshot: Mapping[str, object], path: str | Path | None = None) -> str:
        payload = json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True)
        if path is not None:
            Path(path).write_text(payload, encoding="utf-8")
        return payload

    def export_prometheus(self, provider_metrics: Mapping[str, Mapping[str, object]]) -> str:
        lines = ["# HELP ntpe_provider_requests_total Provider request count", "# TYPE ntpe_provider_requests_total counter"]
        for provider, metrics in provider_metrics.items():
            label = provider.replace('"', "")
            for key in ("request_count", "success_count", "failure_count", "retry_count", "fallback_count", "streaming_count"):
                value = metrics.get(key, 0)
                metric_key = key.replace("_count", "")
                lines.append(f'ntpe_provider_{metric_key}_total{{provider="{label}"}} {value}')
            lines.append(f'ntpe_provider_latency_average_ms{{provider="{label}"}} {metrics.get("average_latency_ms", 0.0)}')
            lines.append(f'ntpe_provider_latency_p95_ms{{provider="{label}"}} {metrics.get("p95_latency_ms", 0.0)}')
            lines.append(f'ntpe_provider_cost_total{{provider="{label}"}} {metrics.get("total_cost", 0.0)}')
            lines.append(f'ntpe_provider_tokens_total{{provider="{label}"}} {metrics.get("total_tokens", 0)}')
        return "\n".join(lines) + "\n"
