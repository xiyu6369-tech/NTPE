"""Adapter helpers for NTPE Foundation-05.5 Pipeline Metrics."""

from __future__ import annotations

from typing import Any, Dict

from core.pipeline.metrics import (
    PipelineMetricsCollector,
    collect_lifecycle_metrics,
    create_metrics_snapshot,
    export_metrics_manifest,
    normalize_metric_record,
    validate_metrics_snapshot,
)


def build_pipeline_metrics_adapter(metrics_id: str = "pipeline") -> PipelineMetricsCollector:
    return PipelineMetricsCollector(metrics_id=metrics_id)


def adapter_metric_record(record: Any) -> Dict[str, Any]:
    return normalize_metric_record(record).to_dict()


def adapter_collect_lifecycle_metrics(result_or_state: Any, metrics_id: str = "pipeline") -> Dict[str, Any]:
    return collect_lifecycle_metrics(result_or_state, metrics_id=metrics_id).to_dict()


def adapter_validate_metrics_snapshot(snapshot: Any) -> bool:
    return validate_metrics_snapshot(snapshot)


def adapter_export_metrics_manifest(snapshot_or_collector: Any) -> Dict[str, Any]:
    if isinstance(snapshot_or_collector, PipelineMetricsCollector):
        return snapshot_or_collector.manifest()
    return export_metrics_manifest(snapshot_or_collector)
