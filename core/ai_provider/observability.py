from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

from .contracts import ProviderError, ProviderRequest, ProviderResponse
from .diagnostics import ProviderRuntimeDiagnostics
from .telemetry_events import (
    TELEMETRY_PROVIDER_HEALTH,
    TELEMETRY_REQUEST_COMPLETED,
    TELEMETRY_REQUEST_FAILED,
    TELEMETRY_REQUEST_STARTED,
    TELEMETRY_ROUTING_DECISION,
    ProviderTelemetryEvent,
)
from .telemetry_exporter import ProviderTelemetryExporter
from .telemetry_metrics import ProviderTelemetryMetrics
from .telemetry_sink import ProviderTelemetrySink
from .telemetry_trace import ProviderTraceRecorder, ProviderTraceSpan


@dataclass
class ProviderObservabilityRuntime:
    """Stage-14.5 provider observability facade.

    It can wrap direct provider execution, Stage-14.3 execution policies, or
    Stage-14.4 load balancers without changing their public APIs.
    """

    sink: ProviderTelemetrySink = field(default_factory=ProviderTelemetrySink)
    traces: ProviderTraceRecorder = field(default_factory=ProviderTraceRecorder)
    exporter: ProviderTelemetryExporter = field(default_factory=ProviderTelemetryExporter)
    diagnostics: ProviderRuntimeDiagnostics = field(default_factory=ProviderRuntimeDiagnostics)
    provider_metrics: Dict[str, ProviderTelemetryMetrics] = field(default_factory=dict)

    def metrics_for(self, provider: Optional[str]) -> ProviderTelemetryMetrics:
        return self.provider_metrics.setdefault(provider or "unknown", ProviderTelemetryMetrics())

    def start_request(self, provider: Optional[str], request: ProviderRequest, trace_id: Optional[str] = None) -> ProviderTraceSpan:
        span = self.traces.start_span(
            "provider.request",
            provider=provider,
            trace_id=trace_id,
            model=request.model,
            stream=request.stream,
            prompt_length=len(request.prompt or ""),
        )
        self.sink.emit(
            ProviderTelemetryEvent(
                TELEMETRY_REQUEST_STARTED,
                provider=provider,
                trace_id=span.trace_id,
                span_id=span.span_id,
                attributes={"model": request.model, "stream": request.stream},
            )
        )
        return span

    def complete_request(self, span: ProviderTraceSpan, response: ProviderResponse, retries: int = 0, fallback: bool = False) -> None:
        span.finish("ok", model=response.model, latency_ms=response.latency_ms)
        self.metrics_for(response.provider).record_success(
            latency_ms=response.latency_ms or span.duration_ms,
            tokens=response.usage.total_tokens,
            cost=response.cost.total_cost,
            retries=retries,
            streaming=bool(response.metadata.get("stream", False)),
            fallback=fallback,
        )
        self.sink.emit(
            ProviderTelemetryEvent(
                TELEMETRY_REQUEST_COMPLETED,
                provider=response.provider,
                trace_id=span.trace_id,
                span_id=span.span_id,
                attributes={"latency_ms": response.latency_ms or span.duration_ms, "tokens": response.usage.total_tokens, "cost": response.cost.total_cost},
            )
        )

    def fail_request(self, span: ProviderTraceSpan, provider: Optional[str], error: Exception, retries: int = 0) -> None:
        span.finish("error", error=str(error))
        self.metrics_for(provider).record_failure(latency_ms=span.duration_ms, retries=retries)
        self.sink.emit(
            ProviderTelemetryEvent(
                TELEMETRY_REQUEST_FAILED,
                provider=provider,
                trace_id=span.trace_id,
                span_id=span.span_id,
                attributes={"error": str(error)},
            )
        )

    def record_routing_decision(self, selected_provider: Optional[str], candidates: list[str], strategy: str = "default") -> None:
        self.sink.emit(
            ProviderTelemetryEvent(
                TELEMETRY_ROUTING_DECISION,
                provider=selected_provider,
                attributes={"selected_provider": selected_provider, "candidates": list(candidates), "strategy": strategy},
            )
        )

    def record_health(self, provider: str, health: Mapping[str, Any]) -> None:
        self.sink.emit(ProviderTelemetryEvent(TELEMETRY_PROVIDER_HEALTH, provider=provider, attributes=dict(health)))

    def execute_provider(self, provider, request: ProviderRequest) -> ProviderResponse:
        provider_name = getattr(provider, "name", None)
        span = self.start_request(provider_name, request)
        try:
            response = provider.complete(request)
            self.complete_request(span, response)
            return response
        except Exception as exc:
            self.fail_request(span, provider_name, exc)
            raise

    def execute_policy(self, execution_policy, provider, request: ProviderRequest):
        provider_name = getattr(provider, "name", None)
        span = self.start_request(provider_name, request)
        try:
            result = execution_policy.execute(provider, request)
            self.complete_request(span, result.response, retries=getattr(result, "retry_count", 0))
            return result
        except ProviderError as exc:
            self.fail_request(span, provider_name, exc)
            raise

    def execute_load_balancer(self, load_balancer, request: ProviderRequest):
        span = self.start_request("load_balancer", request)
        candidates = load_balancer.route(request)
        self.record_routing_decision(None, candidates, strategy="load_balancer")
        try:
            result = load_balancer.execute(request)
            self.record_routing_decision(result.selected_provider, candidates, strategy="load_balancer")
            self.complete_request(span, result.response, retries=getattr(result.execution_result, "retry_count", 0), fallback=result.fallback_used)
            return result
        except ProviderError as exc:
            self.fail_request(span, "load_balancer", exc)
            raise

    def snapshot(self) -> Dict[str, object]:
        metrics = {provider: values.snapshot() for provider, values in self.provider_metrics.items()}
        return {
            "component": "provider_observability_runtime",
            "stage": "NTPE 1.2 Professional Stage-14.5",
            "provider_metrics": metrics,
            "diagnostics": self.diagnostics.evaluate(metrics),
            "events": self.sink.snapshot(),
            "traces": self.traces.snapshot(),
        }

    def export_json(self, path: str | None = None) -> str:
        return self.exporter.export_json(self.snapshot(), path)

    def export_prometheus(self) -> str:
        metrics = {provider: values.snapshot() for provider, values in self.provider_metrics.items()}
        return self.exporter.export_prometheus(metrics)

    def manifest(self) -> Dict[str, object]:
        snapshot = self.snapshot()
        return {
            "component": snapshot["component"],
            "stage": snapshot["stage"],
            "providers": list(self.provider_metrics.keys()),
            "event_count": len(self.sink.events),
            "trace_count": len(self.traces.spans),
            "diagnostics": snapshot["diagnostics"],
        }
