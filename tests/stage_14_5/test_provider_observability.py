from core.ai_provider import (
    MockProvider,
    ProviderLoadBalancer,
    ProviderObservabilityRuntime,
    ProviderRequest,
    ProviderRegistry,
    ProviderRuntimeExecutionPolicy,
    ProviderRuntimeTelemetry,
    TELEMETRY_REQUEST_COMPLETED,
)


def test_observability_records_direct_provider_execution():
    runtime = ProviderObservabilityRuntime()
    provider = MockProvider(name="nvidia", response_text="ok")

    response = runtime.execute_provider(provider, ProviderRequest(prompt="hello world"))
    snapshot = runtime.snapshot()

    assert response.text == "ok"
    assert snapshot["stage"] == "NTPE 1.2 Professional Stage-14.5"
    assert snapshot["provider_metrics"]["nvidia"]["success_count"] == 1
    assert any(event["event_type"] == TELEMETRY_REQUEST_COMPLETED for event in snapshot["events"])
    assert len(snapshot["traces"]) == 1


def test_observability_wraps_execution_policy_without_api_breakage():
    runtime = ProviderObservabilityRuntime()
    policy = ProviderRuntimeExecutionPolicy()
    provider = MockProvider(name="openai", response_text="translated")

    result = runtime.execute_policy(policy, provider, ProviderRequest(prompt="translate me"))

    assert result.response.provider == "openai"
    assert runtime.snapshot()["provider_metrics"]["openai"]["request_count"] == 1
    assert "provider_observability_runtime" in runtime.export_json()


def test_observability_wraps_load_balancer_and_exports_prometheus():
    registry = ProviderRegistry()
    registry.register(MockProvider(name="gemini", response_text="gemini ok"), default=True)
    registry.register(MockProvider(name="anthropic", response_text="anthropic ok"))
    balancer = ProviderLoadBalancer(registry)
    runtime = ProviderObservabilityRuntime()

    result = runtime.execute_load_balancer(balancer, ProviderRequest(prompt="route this"))
    prometheus = runtime.export_prometheus()

    assert result.selected_provider in {"gemini", "anthropic"}
    assert "ntpe_provider_requests_total" in prometheus
    assert runtime.manifest()["stage"] == "NTPE 1.2 Professional Stage-14.5"


def test_runtime_telemetry_entrypoint_and_diagnostics():
    telemetry = ProviderRuntimeTelemetry()
    provider = MockProvider(name="ollama", response_text="local")

    telemetry.observability.execute_provider(provider, ProviderRequest(prompt="local prompt"))
    manifest = telemetry.manifest()
    snapshot = telemetry.snapshot()

    assert manifest["component"] == "provider_runtime_telemetry"
    assert snapshot["diagnostics"]["healthy"] is True
    assert snapshot["diagnostics"]["providers"]["ollama"]["healthy"] is True
