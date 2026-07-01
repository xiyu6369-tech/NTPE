"""Adapter helpers for Foundation-05.2 Pipeline Dependency Resolver."""

from __future__ import annotations

from typing import Any, Dict

from core.pipeline.dependency_resolver import (
    PipelineDependencyResolver,
    create_dependency_resolver,
    normalize_dependency_rule,
    resolve_stage_dependencies,
    validate_dependency_plan,
)
from core.pipeline.stage_registry import PipelineStageRegistry


def build_dependency_resolver_adapter(registry_or_stages: Any = None) -> PipelineDependencyResolver:
    return create_dependency_resolver(registry_or_stages)


def adapter_resolve_dependencies(registry_or_stages: Any, enabled_only: bool = True, strict: bool = True) -> Dict[str, Any]:
    plan = resolve_stage_dependencies(registry_or_stages, enabled_only=enabled_only, strict=strict)
    return plan.to_dict()


def adapter_validate_dependency_plan(plan: Any) -> bool:
    return validate_dependency_plan(plan)


def adapter_dependency_rule(stage: Any) -> Dict[str, Any]:
    return normalize_dependency_rule(stage).to_dict()


def adapter_export_dependency_manifest(resolver: PipelineDependencyResolver, plan: Any) -> Dict[str, Any]:
    return resolver.export_plan_manifest(plan)
