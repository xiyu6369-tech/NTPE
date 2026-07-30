# =====================================================
# NTPE 1.2 Professional
# Stage-17.3 Resource Optimizer Launcher
# =====================================================

from core.workflow.resource_context import ResourceContext
from core.workflow.resource_optimizer import ResourceOptimizer
from core.workflow.resource_profile import ResourceProfile


def check(name, condition):
    status = "PASS" if condition else "FAIL"
    print(f"{name:<36} {status}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE 1.2 Professional - Stage-17.3 Resource Optimizer")
    print("=" * 62)
    profile = ResourceProfile(provider="nvidia", model="default", cost_per_1k_tokens=0.0, requests_per_minute=40)
    result = ResourceOptimizer().optimize(ResourceContext(job_count=5, estimated_tokens=5000, profiles=[profile], cache_hit_rate=0.2))
    check("Optimizer Result", result.success)
    check("Provider Selected", result.selected_plan.provider == "nvidia")
    check("Cache Savings", result.selected_plan.cache_savings_tokens == 1000)
    check("Metrics Created", result.metrics["candidate_count"] == 1)
    print("PASS")


if __name__ == "__main__":
    main()
