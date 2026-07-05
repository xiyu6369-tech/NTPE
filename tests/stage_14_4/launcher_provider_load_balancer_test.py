from core.ai_provider import (
    FallbackChain,
    MockProvider,
    MultiProviderOrchestrator,
    ProviderLoadBalancer,
    ProviderPool,
    ProviderPoolEntry,
    ProviderRegistry,
    ProviderRequest,
    RoutingPolicy,
)


def check(label, condition):
    print(f"{label:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE 1.2 Professional Stage-14.4 Provider Load Balancer Test")
    print("=" * 68)
    registry = ProviderRegistry()
    registry.register(MockProvider(name="primary", response_text="primary", fail_times=3), default=True)
    registry.register(MockProvider(name="backup", response_text="backup"))
    pool = ProviderPool([
        ProviderPoolEntry("primary", weight=10, priority=1),
        ProviderPoolEntry("backup", weight=1, priority=2),
    ])
    balancer = ProviderLoadBalancer(
        registry,
        pool=pool,
        routing_policy=RoutingPolicy(mode="priority"),
        fallback_chain=FallbackChain(["primary", "backup"]),
    )
    result = balancer.execute(ProviderRequest(prompt="hello"))
    check("Fallback Used", result.fallback_used)
    check("Backup Selected", result.selected_provider == "backup")
    check("Attempts Recorded", len(result.attempts) == 2)
    check("Statistics Recorded", balancer.statistics["backup"]["success_count"] == 1)
    check("Manifest", balancer.manifest()["stage"] == "NTPE 1.2 Professional Stage-14.4")
    orchestrator = MultiProviderOrchestrator(registry=registry, load_balancer=balancer)
    check("Orchestrator Manifest", orchestrator.manifest()["component"] == "multi_provider_orchestrator")
    print("PASS")


if __name__ == "__main__":
    main()
