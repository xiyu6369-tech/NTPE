"""Adapter helpers for Foundation-05.3 Pipeline Scheduler."""

from __future__ import annotations

from typing import Any, Dict

from core.pipeline.scheduler import (
    PipelineScheduler,
    create_pipeline_scheduler,
    normalize_schedule_item,
    schedule_pipeline,
    validate_schedule,
)


def build_pipeline_scheduler_adapter(registry_or_stages: Any = None) -> PipelineScheduler:
    return create_pipeline_scheduler(registry_or_stages)


def adapter_schedule_pipeline(registry_or_stages: Any, strict: bool = True) -> Dict[str, Any]:
    return schedule_pipeline(registry_or_stages, strict=strict).to_dict()


def adapter_validate_schedule(schedule: Any) -> bool:
    return validate_schedule(schedule)


def adapter_schedule_item(item: Any) -> Dict[str, Any]:
    return normalize_schedule_item(item).to_dict(include_stage=False)


def adapter_export_schedule_manifest(scheduler: PipelineScheduler, schedule: Any) -> Dict[str, Any]:
    return scheduler.export_manifest(schedule)
