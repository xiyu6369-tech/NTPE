# =====================================================
# NTPE 1.2 Professional
# Stage-17.3 Resource Optimizer Unit Tests
# =====================================================

from core.workflow.resource_context import ResourceContext
from core.workflow.resource_optimizer import ResourceOptimizer
from core.workflow.resource_profile import ResourceProfile
from core.workflow.resource_registry import ResourceProfileRegistry


def test_resource_optimizer_selects_low_cost_profile():
    profiles = [
        ResourceProfile(provider="expensive", model="a", cost_per_1k_tokens=0.5, requests_per_minute=60),
        ResourceProfile(provider="cheap", model="b", cost_per_1k_tokens=0.01, requests_per_minute=60),
    ]
    result = ResourceOptimizer().optimize(ResourceContext(job_count=2, estimated_tokens=2000, profiles=profiles))
    assert result.success
    assert result.selected_plan.provider == "cheap"


def test_resource_optimizer_accounts_for_cache_savings():
    profile = ResourceProfile(provider="cache", model="m", cost_per_1k_tokens=0.1, cache_enabled=True)
    result = ResourceOptimizer().optimize(ResourceContext(job_count=1, estimated_tokens=1000, cache_hit_rate=0.5, profiles=[profile]))
    assert result.selected_plan.cache_savings_tokens == 500
    assert result.selected_plan.estimated_tokens == 500


def test_resource_registry_roundtrip():
    profile = ResourceProfile(provider="nvidia", model="llama")
    registry = ResourceProfileRegistry([profile])
    assert registry.get("nvidia", "llama") == profile
    assert len(registry.list()) == 1
