"""Adapter helpers for Foundation-05.4 Pipeline Lifecycle Manager."""

from __future__ import annotations

from typing import Any, Dict

from core.pipeline.lifecycle_manager import (
    PipelineLifecycleManager,
    create_lifecycle_manager,
    normalize_lifecycle_event,
    run_pipeline_lifecycle,
    validate_lifecycle_state,
)


def build_pipeline_lifecycle_adapter(schedule_or_registry: Any, lifecycle_id: str = "pipeline") -> PipelineLifecycleManager:
    return create_lifecycle_manager(schedule_or_registry, lifecycle_id=lifecycle_id)


def adapter_run_lifecycle(schedule_or_registry: Any, payload: Any = None, lifecycle_id: str = "pipeline") -> Dict[str, Any]:
    return run_pipeline_lifecycle(schedule_or_registry, payload=payload, lifecycle_id=lifecycle_id).to_dict()


def adapter_validate_lifecycle_state(state: Any) -> bool:
    return validate_lifecycle_state(state)


def adapter_lifecycle_event(event: Any) -> Dict[str, Any]:
    return normalize_lifecycle_event(event).to_dict()


def adapter_export_lifecycle_manifest(manager: PipelineLifecycleManager) -> Dict[str, Any]:
    return manager.export_manifest()
