"""Adapter helpers for Foundation-05.1 Pipeline Stage Registry."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from core.pipeline.stage_registry import (
    PipelineStageRegistry,
    create_stage_registry,
    normalize_stage_definition,
    validate_stage_definition,
)


def build_stage_registry_adapter(stages: Optional[Iterable[Any]] = None) -> PipelineStageRegistry:
    return create_stage_registry(stages)


def adapter_register_stage(registry: PipelineStageRegistry, stage: Any, **overrides: Any) -> Dict[str, Any]:
    definition = registry.register(stage, **overrides)
    return definition.to_dict()


def adapter_validate_stage(stage: Any) -> bool:
    definition = normalize_stage_definition(stage)
    return validate_stage_definition(definition)


def adapter_export_stage_manifest(registry: PipelineStageRegistry) -> Dict[str, Any]:
    return registry.export_manifest()
