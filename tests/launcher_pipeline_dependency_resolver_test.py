import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.pipeline.stage_registry import create_stage_registry
from core.pipeline.dependency_resolver import (
    PipelineDependencyPlan,
    create_dependency_resolver,
    normalize_dependency_rule,
    resolve_stage_dependencies,
    validate_dependency_plan,
)
from adapters.pipeline_dependency_resolver_adapter import (
    adapter_dependency_rule,
    adapter_export_dependency_manifest,
    adapter_resolve_dependencies,
    adapter_validate_dependency_plan,
    build_dependency_resolver_adapter,
)


def mark(name, ok):
    if not ok:
        raise AssertionError(name)
    print(f"{name:<26} PASS")


def main():
    print("NTPE Foundation-05.2 Pipeline Dependency Resolver Test")
    print("=" * 62)

    legacy = {"name": "prompt", "dependencies": ["context"], "metadata": {"after": ["context"]}}
    rule = normalize_dependency_rule(legacy)
    mark("Legacy Rule", rule.stage_id == "prompt@1.0.0")
    mark("Rule Requires", rule.requires == ("context",))

    registry = create_stage_registry()
    registry.register({"name": "quality", "priority": 30, "dependencies": ["prompt"]})
    registry.register({"name": "context", "priority": 10})
    registry.register({"name": "prompt", "priority": 20, "dependencies": ["context"]})
    registry.register({"name": "narrative", "priority": 25, "metadata": {"after": ["prompt"], "before": ["quality"]}})
    mark("Registry Ready", registry.exists("context") and registry.exists("quality"))

    resolver = create_dependency_resolver(registry)
    mark("Resolver Created", resolver is not None)
    plan = resolver.resolve()
    mark("Plan Created", isinstance(plan, PipelineDependencyPlan))
    mark("Validate Plan", validate_dependency_plan(plan) is True)
    mark("Plan Valid", plan.valid is True)
    mark("Order Context", plan.ordered_stage_ids[0] == "context@1.0.0")
    mark("Order Quality", plan.ordered_stage_ids[-1] == "quality@1.0.0")
    mark("Edges Created", ("context@1.0.0", "prompt@1.0.0") in plan.edges)

    manifest = resolver.export_plan_manifest(plan)
    mark("Manifest Created", manifest["schema"] == "ntpe.pipeline.dependency_resolver.v1")
    mark("Resolver Events", len(manifest["events"]) >= 1)

    registry.disable("prompt")
    disabled_plan = create_dependency_resolver(registry).resolve(enabled_only=True, strict=True)
    mark("Disabled Detected", "prompt@1.0.0" in disabled_plan.disabled)
    mark("Missing Detected", "prompt" in disabled_plan.missing)
    mark("Strict Invalid", disabled_plan.valid is False)

    loose_plan = create_dependency_resolver(registry).resolve(enabled_only=True, strict=False)
    mark("Loose Plan", loose_plan.valid is False and "quality@1.0.0" in loose_plan.ordered_stage_ids)

    cycle_registry = create_stage_registry([
        {"name": "a", "dependencies": ["c"]},
        {"name": "b", "dependencies": ["a"]},
        {"name": "c", "dependencies": ["b"]},
    ])
    cycle_plan = resolve_stage_dependencies(cycle_registry)
    mark("Cycle Detected", cycle_plan.valid is False and len(cycle_plan.cycles) == 1)

    adapter_resolver = build_dependency_resolver_adapter(cycle_registry)
    mark("Adapter Created", adapter_resolver is not None)
    adapter_plan = adapter_resolve_dependencies(cycle_registry)
    mark("Adapter Resolve", adapter_plan["valid"] is False)
    mark("Adapter Rule", adapter_dependency_rule({"name": "x", "after": ["a"]})["after"] == ["a"])
    mark("Adapter Validate", adapter_validate_dependency_plan(plan) is True)
    adapter_manifest = adapter_export_dependency_manifest(resolver, plan)
    mark("Adapter Manifest", adapter_manifest["plan"]["valid"] is True)

    compat = create_stage_registry([
        {"name": "context", "priority": 10},
        {"name": "prompt", "priority": 20, "dependencies": ["context"]},
    ])
    compat_plan = resolve_stage_dependencies(compat)
    mark("Backward Compatible", compat_plan.ordered_stage_ids == ("context@1.0.0", "prompt@1.0.0"))
    print("PASS")


if __name__ == "__main__":
    main()
