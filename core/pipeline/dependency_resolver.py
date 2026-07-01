"""
NTPE Foundation-05.2 Pipeline Dependency Resolver

Incremental dependency layer for Pipeline Stage Registry.  It resolves stage
execution order using stable contract fields while remaining compatible with
legacy manifests/dicts from Foundation-05.1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

from core.pipeline.stage_registry import (
    PipelineStageDefinition,
    PipelineStageRegistry,
    create_stage_registry,
    normalize_stage_definition,
)


@dataclass(frozen=True)
class PipelineDependencyRule:
    """Normalized dependency hints for one stage."""

    stage_id: str
    requires: Tuple[str, ...] = field(default_factory=tuple)
    before: Tuple[str, ...] = field(default_factory=tuple)
    after: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "requires": list(self.requires),
            "before": list(self.before),
            "after": list(self.after),
        }


@dataclass(frozen=True)
class PipelineDependencyPlan:
    """Resolved dependency plan consumed by later scheduler/runtime layers."""

    ordered_stage_ids: Tuple[str, ...]
    edges: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    missing: Tuple[str, ...] = field(default_factory=tuple)
    disabled: Tuple[str, ...] = field(default_factory=tuple)
    cycles: Tuple[Tuple[str, ...], ...] = field(default_factory=tuple)
    valid: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "ntpe.pipeline.dependency_plan.v1",
            "ordered_stage_ids": list(self.ordered_stage_ids),
            "edges": [list(edge) for edge in self.edges],
            "missing": list(self.missing),
            "disabled": list(self.disabled),
            "cycles": [list(cycle) for cycle in self.cycles],
            "valid": self.valid,
        }


def _as_tuple(value: Any) -> Tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value if str(item))


def normalize_dependency_rule(stage: Any) -> PipelineDependencyRule:
    """Normalize registry stage, legacy dict, or manifest item into a rule."""

    if isinstance(stage, PipelineStageDefinition):
        data = stage.to_dict()
    elif isinstance(stage, Mapping):
        data = dict(stage)
    else:
        data = normalize_stage_definition(stage).to_dict()

    metadata = dict(data.get("metadata") or {})
    stage_id = data.get("stage_id") or f"{data.get('name')}@{data.get('version', '1.0.0')}"
    requires = data.get("requires") or data.get("dependencies") or metadata.get("requires") or metadata.get("dependencies")
    before = data.get("before") or metadata.get("before")
    after = data.get("after") or metadata.get("after")
    return PipelineDependencyRule(
        stage_id=str(stage_id),
        requires=_as_tuple(requires),
        before=_as_tuple(before),
        after=_as_tuple(after),
    )


def validate_dependency_plan(plan: PipelineDependencyPlan) -> bool:
    if not isinstance(plan, PipelineDependencyPlan):
        raise TypeError("plan must be PipelineDependencyPlan")
    if plan.valid and (plan.missing or plan.cycles):
        raise ValueError("valid dependency plan cannot contain missing stages or cycles")
    return True


class PipelineDependencyResolver:
    """Resolve Stage Registry entries into deterministic execution order."""

    def __init__(self, registry: Optional[PipelineStageRegistry] = None) -> None:
        self.registry = registry or create_stage_registry()
        self.events: List[Dict[str, Any]] = []

    def resolve(self, enabled_only: bool = True, strict: bool = True) -> PipelineDependencyPlan:
        stages = self.registry.list(enabled_only=enabled_only)
        active_by_id: Dict[str, PipelineStageDefinition] = {stage.stage_id: stage for stage in stages}
        name_to_id: Dict[str, str] = {stage.name: stage.stage_id for stage in stages}

        disabled_ids: Set[str] = set()
        if enabled_only:
            disabled_ids = {stage.stage_id for stage in self.registry.list(enabled_only=False) if not stage.enabled}

        edges: Set[Tuple[str, str]] = set()
        missing: Set[str] = set()

        def resolve_ref(ref: str) -> Optional[str]:
            if ref in active_by_id:
                return ref
            if ref in name_to_id:
                return name_to_id[ref]
            if "@" not in ref and self.registry.exists(ref):
                try:
                    candidate = self.registry.get(ref).stage_id
                    if candidate in disabled_ids:
                        return candidate
                except Exception:
                    pass
            return None

        for stage in stages:
            rule = normalize_dependency_rule(stage)
            for dep in rule.requires:
                dep_id = resolve_ref(dep)
                if dep_id and dep_id in active_by_id:
                    edges.add((dep_id, stage.stage_id))
                else:
                    missing.add(dep)
            for predecessor in rule.after:
                pred_id = resolve_ref(predecessor)
                if pred_id and pred_id in active_by_id:
                    edges.add((pred_id, stage.stage_id))
                else:
                    missing.add(predecessor)
            for successor in rule.before:
                succ_id = resolve_ref(successor)
                if succ_id and succ_id in active_by_id:
                    edges.add((stage.stage_id, succ_id))
                else:
                    missing.add(successor)

        ordered, cycles = self._topological_sort(active_by_id, edges)
        valid = not missing and not cycles
        if strict and not valid:
            plan = PipelineDependencyPlan(tuple(ordered), tuple(sorted(edges)), tuple(sorted(missing)), tuple(sorted(disabled_ids)), tuple(cycles), False)
            self.events.append({"type": "dependency_resolve_failed", "plan": plan.to_dict()})
            return plan

        plan = PipelineDependencyPlan(tuple(ordered), tuple(sorted(edges)), tuple(sorted(missing)), tuple(sorted(disabled_ids)), tuple(cycles), valid)
        self.events.append({"type": "dependency_resolved", "plan": plan.to_dict()})
        return plan

    def _topological_sort(self, stages: Mapping[str, PipelineStageDefinition], edges: Set[Tuple[str, str]]) -> Tuple[List[str], List[Tuple[str, ...]]]:
        stage_ids = set(stages.keys())
        outgoing: Dict[str, Set[str]] = {sid: set() for sid in stage_ids}
        incoming_count: Dict[str, int] = {sid: 0 for sid in stage_ids}
        for left, right in edges:
            if left in stage_ids and right in stage_ids and right not in outgoing[left]:
                outgoing[left].add(right)
                incoming_count[right] += 1

        def sort_key(stage_id: str) -> Tuple[int, str]:
            stage = stages[stage_id]
            return (stage.priority, stage.name)

        ready = sorted([sid for sid, count in incoming_count.items() if count == 0], key=sort_key)
        ordered: List[str] = []
        while ready:
            current = ready.pop(0)
            ordered.append(current)
            for nxt in sorted(outgoing[current], key=sort_key):
                incoming_count[nxt] -= 1
                if incoming_count[nxt] == 0:
                    ready.append(nxt)
                    ready.sort(key=sort_key)

        cycles: List[Tuple[str, ...]] = []
        if len(ordered) != len(stage_ids):
            remaining = tuple(sorted(stage_ids - set(ordered)))
            cycles.append(remaining)
            # Preserve deterministic partial output for diagnostics.
            ordered.extend([sid for sid in sorted(remaining, key=sort_key) if sid not in ordered])
        return ordered, cycles

    def export_plan_manifest(self, plan: PipelineDependencyPlan) -> Dict[str, Any]:
        return {
            "schema": "ntpe.pipeline.dependency_resolver.v1",
            "plan": plan.to_dict(),
            "events": list(self.events),
        }


def create_dependency_resolver(registry_or_stages: Optional[Any] = None) -> PipelineDependencyResolver:
    if isinstance(registry_or_stages, PipelineStageRegistry):
        return PipelineDependencyResolver(registry_or_stages)
    registry = create_stage_registry(registry_or_stages or [])
    return PipelineDependencyResolver(registry)


def resolve_stage_dependencies(registry_or_stages: Any, enabled_only: bool = True, strict: bool = True) -> PipelineDependencyPlan:
    return create_dependency_resolver(registry_or_stages).resolve(enabled_only=enabled_only, strict=strict)
