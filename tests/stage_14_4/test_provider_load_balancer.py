from core.ai_provider import (
    FallbackChain,
    MockProvider,
    ModelInfo,
    ProviderLoadBalancer,
    ProviderPool,
    ProviderPoolEntry,
    ProviderRegistry,
    ProviderRequest,
    RoutingPolicy,
)


def build_registry():
    registry = ProviderRegistry()
    registry.register(MockProvider(name="fast", response_text="fast ok", models=[ModelInfo(id="m", provider="fast", supports_streaming=True)]), default=True)
    registry.register(MockProvider(name="backup", response_text="backup ok", models=[ModelInfo(id="m", provider="backup", supports_streaming=True)]))
    return registry


def test_weighted_routing_selects_highest_weight():
    registry = build_registry()
    pool = ProviderPool([
        ProviderPoolEntry("fast", weight=1.0, priority=20),
        ProviderPoolEntry("backup", weight=5.0, priority=50),
    ])
    balancer = ProviderLoadBalancer(registry, pool=pool, routing_policy=RoutingPolicy(mode="weighted"))
    result = balancer.execute(ProviderRequest(prompt="hello"))
    assert result.selected_provider == "backup"
    assert result.response.text == "backup ok"


def test_fallback_chain_uses_backup_after_failure():
    registry = ProviderRegistry()
    registry.register(MockProvider(name="primary", response_text="primary", fail_times=5), default=True)
    registry.register(MockProvider(name="backup", response_text="backup"))
    pool = ProviderPool(["primary", "backup"])
    balancer = ProviderLoadBalancer(
        registry,
        pool=pool,
        routing_policy=RoutingPolicy(mode="priority"),
        fallback_chain=FallbackChain(["primary", "backup"]),
    )
    result = balancer.execute(ProviderRequest(prompt="hello"))
    assert result.selected_provider == "backup"
    assert result.fallback_used is True
    assert [a.provider for a in result.attempts] == ["primary", "backup"]


def test_capability_aware_routing_filters_streaming():
    registry = build_registry()
    request = ProviderRequest(prompt="stream", stream=True)
    balancer = ProviderLoadBalancer(registry, routing_policy=RoutingPolicy(mode="capability_aware"))
    assert balancer.route(request)


def test_manifest_exposes_stage_14_4():
    balancer = ProviderLoadBalancer(build_registry())
    manifest = balancer.manifest()
    assert manifest["stage"] == "NTPE 1.2 Professional Stage-14.4"
    assert manifest["component"] == "provider_load_balancer"
