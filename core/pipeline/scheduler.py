"""
NTPE Foundation-05.3 Pipeline Scheduler

Incremental scheduler layer for turning a Foundation-05.2 dependency plan into
an executable, auditable pipeline schedule.  This module does not execute stage
handlers; it only produces stable schedule items for later lifecycle/runtime
layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from core.pipeline.dependency_resolver import (
    PipelineDependencyPlan,
    PipelineDependencyResolver,
    create_dependency_resolver,
    resolve_stage_dependencies,
)
from core.pipeline.stage_registry import PipelineStageDefinition, PipelineStageRegistry


SCHEDULE_ITEM_READY = "ready"
SCHEDULE_ITEM_SKIPPED = "skipped"
SCHEDULE_ITEM_BLOCKED = "blocked"


@dataclass(frozen=True)
class PipelineScheduleItem:
    """One scheduled stage entry produced from a dependency plan."""

    stage_id: str
    index: int
    status: str = SCHEDULE_ITEM_READY
    reason: str = ""
    stage: Optional[PipelineStageDefinition] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self, include_stage: bool = True) -> Dict[str, Any]:
        data = {
            "stage_id": self.stage_id,
            "index": self.index,
            "status": self.status,
            "reason": self.reason,
            "metadata": dict(self.metadata or {}),
        }
        if include_stage and self.stage is not None:
            data["stage"] = self.stage.to_dict()
        return data


@dataclass(frozen=True)
class PipelineSchedule:
    """Resolved schedule manifest consumed by Foundation-05.4+ runtime layers."""

    items: Tuple[PipelineScheduleItem, ...]
    valid: bool = True
    blocked: Tuple[str, ...] = field(default_factory=tuple)
    skipped: Tuple[str, ...] = field(default_factory=tuple)
    source_plan: Optional[PipelineDependencyPlan] = None
    events: Tuple[Mapping[str, Any], ...] = field(default_factory=tuple)

    @property
    def ordered_stage_ids(self) -> Tuple[str, ...]:
        return tuple(item.stage_id for item in self.items if item.status == SCHEDULE_ITEM_READY)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "ntpe.pipeline.schedule.v1",
            "valid": self.valid,
            "ordered_stage_ids": list(self.ordered_stage_ids),
            "blocked": list(self.blocked),
            "skipped": list(self.skipped),
            "items": [item.to_dict() for item in self.items],
            "source_plan": self.source_plan.to_dict() if self.source_plan else None,
            "events": [dict(event) for event in self.events],
        }


def normalize_schedule_item(item: Any, index: Optional[int] = None) -> PipelineScheduleItem:
    """Normalize legacy strings/dicts/stages into a schedule item."""

    if isinstance(item, PipelineScheduleItem):
        return item
    if isinstance(item, PipelineStageDefinition):
        return PipelineScheduleItem(stage_id=item.stage_id, index=0 if index is None else index, stage=item)
    if isinstance(item, str):
        return PipelineScheduleItem(stage_id=item, index=0 if index is None else index)
    if isinstance(item, Mapping):
        return PipelineScheduleItem(
            stage_id=str(item.get("stage_id") or item.get("id") or item.get("name")),
            index=int(item.get("index", 0 if index is None else index)),
            status=str(item.get("status") or SCHEDULE_ITEM_READY),
            reason=str(item.get("reason") or ""),
            stage=item.get("stage") if isinstance(item.get("stage"), PipelineStageDefinition) else None,
            metadata=dict(item.get("metadata") or {}),
        )
    raise TypeError("unsupported schedule item")


def validate_schedule(schedule: PipelineSchedule) -> bool:
    if not isinstance(schedule, PipelineSchedule):
        raise TypeError("schedule must be PipelineSchedule")
    seen = set()
    for item in schedule.items:
        if item.stage_id in seen:
            raise ValueError(f"duplicate scheduled stage: {item.stage_id}")
        seen.add(item.stage_id)
        if item.status not in {SCHEDULE_ITEM_READY, SCHEDULE_ITEM_SKIPPED, SCHEDULE_ITEM_BLOCKED}:
            raise ValueError(f"invalid schedule item status: {item.status}")
    if schedule.valid and schedule.blocked:
        raise ValueError("valid schedule cannot contain blocked stages")
    return True


class PipelineScheduler:
    """Build deterministic schedules from registry + dependency plan."""

    def __init__(self, registry: Optional[PipelineStageRegistry] = None, resolver: Optional[PipelineDependencyResolver] = None) -> None:
        self.registry = registry
        self.resolver = resolver or (create_dependency_resolver(registry) if registry is not None else None)
        self.events: List[Dict[str, Any]] = []

    def build_schedule(self, plan: Optional[PipelineDependencyPlan] = None, strict: bool = True) -> PipelineSchedule:
        if plan is None:
            if self.resolver is None:
                raise ValueError("scheduler requires a dependency plan or resolver")
            plan = self.resolver.resolve(enabled_only=True, strict=strict)

        items: List[PipelineScheduleItem] = []
        blocked: List[str] = []
        skipped: List[str] = []

        invalid_plan = bool(plan.missing or plan.cycles or not plan.valid)
        for index, stage_id in enumerate(plan.ordered_stage_ids):
            stage = self._get_stage(stage_id)
            if stage is not None and not stage.enabled:
                skipped.append(stage_id)
                item = PipelineScheduleItem(stage_id=stage_id, index=index, status=SCHEDULE_ITEM_SKIPPED, reason="stage disabled", stage=stage)
            elif invalid_plan and strict:
                blocked.append(stage_id)
                item = PipelineScheduleItem(stage_id=stage_id, index=index, status=SCHEDULE_ITEM_BLOCKED, reason="dependency plan invalid", stage=stage)
            else:
                item = PipelineScheduleItem(stage_id=stage_id, index=index, status=SCHEDULE_ITEM_READY, stage=stage)
            items.append(item)
            self.events.append({"type": "schedule_item_created", "stage_id": stage_id, "status": item.status, "index": index})

        valid = not blocked and not plan.missing and not plan.cycles
        schedule = PipelineSchedule(
            items=tuple(items),
            valid=valid,
            blocked=tuple(blocked),
            skipped=tuple(skipped),
            source_plan=plan,
            events=tuple(self.events),
        )
        self.events.append({"type": "schedule_created", "valid": schedule.valid, "count": len(schedule.items)})
        return schedule

    def _get_stage(self, stage_id: str) -> Optional[PipelineStageDefinition]:
        if self.registry is None:
            return None
        try:
            return self.registry.get(stage_id)
        except Exception:
            try:
                name, version = stage_id.rsplit("@", 1)
                return self.registry.get(name, version)
            except Exception:
                return None

    def export_manifest(self, schedule: PipelineSchedule) -> Dict[str, Any]:
        return {
            "schema": "ntpe.pipeline.scheduler.v1",
            "schedule": schedule.to_dict(),
            "events": list(self.events),
        }


def create_pipeline_scheduler(registry_or_stages: Optional[Any] = None) -> PipelineScheduler:
    if isinstance(registry_or_stages, PipelineStageRegistry):
        return PipelineScheduler(registry_or_stages)
    if registry_or_stages is None:
        return PipelineScheduler()
    resolver = create_dependency_resolver(registry_or_stages)
    return PipelineScheduler(resolver.registry, resolver)


def schedule_pipeline(registry_or_stages: Any, strict: bool = True) -> PipelineSchedule:
    scheduler = create_pipeline_scheduler(registry_or_stages)
    plan = resolve_stage_dependencies(scheduler.registry, enabled_only=True, strict=strict)
    return scheduler.build_schedule(plan, strict=strict)
