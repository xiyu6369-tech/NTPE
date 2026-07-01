"""
NTPE Foundation-05.5 Pipeline Metrics

Additive metrics layer for Production Pipeline lifecycle executions.  The module
collects lifecycle counters, event timing, stage outcomes, schedule metadata and
runtime summaries without mutating Foundation-05.4 lifecycle state objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

try:
    from core.pipeline.lifecycle_manager import PipelineLifecycleResult, PipelineLifecycleState
except Exception:  # pragma: no cover - keeps old import paths tolerant
    PipelineLifecycleResult = Any  # type: ignore
    PipelineLifecycleState = Any  # type: ignore

METRICS_SCHEMA = "ntpe.pipeline.metrics.v1"
METRIC_CREATED = "created"
METRIC_RECORDED = "recorded"
METRIC_EXPORTED = "exported"


@dataclass(frozen=True)
class PipelineMetricRecord:
    """Single metric record with stable serialization."""

    name: str
    value: Any
    unit: str = "count"
    category: str = "pipeline"
    stage_id: str = ""
    timestamp: float = field(default_factory=time)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "category": self.category,
            "stage_id": self.stage_id,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata or {}),
        }


@dataclass
class PipelineMetricsSnapshot:
    """Exportable metrics snapshot for one pipeline execution."""

    metrics_id: str
    status: str = METRIC_CREATED
    created_at: float = field(default_factory=time)
    records: List[PipelineMetricRecord] = field(default_factory=list)
    counters: MutableMapping[str, int] = field(default_factory=lambda: {
        "records": 0,
        "events": 0,
        "stages_started": 0,
        "stages_completed": 0,
        "stages_failed": 0,
        "stages_skipped": 0,
        "runs_completed": 0,
        "runs_failed": 0,
        "runs_stopped": 0,
    })
    timings: MutableMapping[str, float] = field(default_factory=dict)
    stage_timings: MutableMapping[str, float] = field(default_factory=dict)
    stage_status: MutableMapping[str, str] = field(default_factory=dict)
    metadata: MutableMapping[str, Any] = field(default_factory=dict)

    def add_record(self, record: Any) -> PipelineMetricRecord:
        metric = normalize_metric_record(record)
        self.records.append(metric)
        self.counters["records"] = len(self.records)
        self.status = METRIC_RECORDED
        return metric

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": METRICS_SCHEMA,
            "metrics_id": self.metrics_id,
            "status": self.status,
            "created_at": self.created_at,
            "counters": dict(self.counters),
            "timings": dict(self.timings),
            "stage_timings": dict(self.stage_timings),
            "stage_status": dict(self.stage_status),
            "metadata": dict(self.metadata),
            "records": [record.to_dict() for record in self.records],
        }


def normalize_metric_record(record: Any) -> PipelineMetricRecord:
    """Normalize legacy metric inputs to PipelineMetricRecord."""

    if isinstance(record, PipelineMetricRecord):
        return record
    if isinstance(record, str):
        return PipelineMetricRecord(name=record, value=1)
    if isinstance(record, Mapping):
        return PipelineMetricRecord(
            name=str(record.get("name") or record.get("metric") or "metric"),
            value=record.get("value", 1),
            unit=str(record.get("unit") or "count"),
            category=str(record.get("category") or "pipeline"),
            stage_id=str(record.get("stage_id") or ""),
            timestamp=float(record.get("timestamp") or time()),
            metadata=dict(record.get("metadata") or {}),
        )
    raise TypeError("unsupported metric record")


def create_metrics_snapshot(metrics_id: str = "pipeline") -> PipelineMetricsSnapshot:
    snapshot = PipelineMetricsSnapshot(metrics_id=str(metrics_id or "pipeline"))
    snapshot.add_record({"name": "metrics_created", "value": 1, "category": "metrics"})
    return snapshot


def validate_metrics_snapshot(snapshot: PipelineMetricsSnapshot) -> bool:
    if not isinstance(snapshot, PipelineMetricsSnapshot):
        raise TypeError("snapshot must be PipelineMetricsSnapshot")
    if not snapshot.metrics_id:
        raise ValueError("metrics_id is required")
    if snapshot.counters.get("records", 0) != len(snapshot.records):
        raise ValueError("record counter mismatch")
    return True


def _event_to_dict(event: Any) -> Dict[str, Any]:
    if hasattr(event, "to_dict"):
        return dict(event.to_dict())
    if isinstance(event, Mapping):
        return dict(event)
    return {"type": str(event), "timestamp": time(), "stage_id": ""}


def _state_from_result(result_or_state: Any) -> Any:
    if hasattr(result_or_state, "state") and getattr(result_or_state, "state") is not None:
        return getattr(result_or_state, "state")
    return result_or_state


def collect_lifecycle_metrics(result_or_state: Any, metrics_id: str = "pipeline") -> PipelineMetricsSnapshot:
    """Collect metrics from PipelineLifecycleResult or PipelineLifecycleState."""

    state = _state_from_result(result_or_state)
    snapshot = create_metrics_snapshot(metrics_id)

    status = str(getattr(state, "status", getattr(result_or_state, "status", "unknown")))
    counters = dict(getattr(state, "counters", {}) or {})
    events = [_event_to_dict(event) for event in list(getattr(state, "events", []) or [])]

    snapshot.metadata["source"] = "lifecycle"
    snapshot.metadata["status"] = status
    snapshot.counters["events"] = len(events)
    snapshot.counters["stages_started"] = int(counters.get("stages_started", 0))
    snapshot.counters["stages_completed"] = int(counters.get("stages_completed", 0))
    snapshot.counters["stages_failed"] = int(counters.get("stages_failed", 0))
    snapshot.counters["stages_skipped"] = int(counters.get("stages_skipped", 0))
    snapshot.counters["runs_completed"] = 1 if status == "completed" else 0
    snapshot.counters["runs_failed"] = 1 if status == "failed" else 0
    snapshot.counters["runs_stopped"] = 1 if status == "stopped" else 0

    started_at = getattr(state, "started_at", None)
    completed_at = getattr(state, "completed_at", None) or getattr(state, "stopped_at", None)
    if started_at and completed_at:
        snapshot.timings["duration_seconds"] = max(0.0, float(completed_at) - float(started_at))

    stage_start: Dict[str, float] = {}
    for event in events:
        name = str(event.get("type") or "")
        stage_id = str(event.get("stage_id") or "")
        timestamp = float(event.get("timestamp") or time())
        stage_key = stage_id.split("@", 1)[0] if stage_id else ""
        if name in {"stage_started", "stage_begin"} and stage_id:
            stage_start[stage_id] = timestamp
            snapshot.stage_status[stage_id] = "running"
            if stage_key:
                snapshot.stage_status[stage_key] = "running"
        elif name in {"stage_completed", "stage_complete"} and stage_id:
            snapshot.stage_status[stage_id] = "completed"
            if stage_key:
                snapshot.stage_status[stage_key] = "completed"
            if stage_id in stage_start:
                duration = max(0.0, timestamp - stage_start[stage_id])
                snapshot.stage_timings[stage_id] = duration
                if stage_key:
                    snapshot.stage_timings[stage_key] = duration
        elif name in {"stage_failed", "lifecycle_failed"} and stage_id:
            snapshot.stage_status[stage_id] = "failed"
            if stage_key:
                snapshot.stage_status[stage_key] = "failed"
        elif name == "stage_skipped" and stage_id:
            snapshot.stage_status[stage_id] = "skipped"
            if stage_key:
                snapshot.stage_status[stage_key] = "skipped"

    for key, value in counters.items():
        snapshot.add_record({"name": str(key), "value": int(value), "category": "counter"})

    snapshot.add_record({"name": "event_count", "value": len(events), "category": "event"})
    snapshot.add_record({"name": "pipeline_status", "value": status, "unit": "status", "category": "pipeline"})
    return snapshot


def merge_metrics_snapshots(metrics_id: str, snapshots: Iterable[PipelineMetricsSnapshot]) -> PipelineMetricsSnapshot:
    merged = create_metrics_snapshot(metrics_id)
    merged.metadata["source"] = "merged"
    for snapshot in snapshots:
        validate_metrics_snapshot(snapshot)
        for key, value in snapshot.counters.items():
            if isinstance(value, int):
                merged.counters[key] = int(merged.counters.get(key, 0)) + value
        for key, value in snapshot.timings.items():
            merged.timings[key] = float(merged.timings.get(key, 0.0)) + float(value)
        for key, value in snapshot.stage_timings.items():
            merged.stage_timings[key] = float(value)
        merged.stage_status.update(snapshot.stage_status)
        for record in snapshot.records:
            merged.add_record(record)
    merged.counters["records"] = len(merged.records)
    return merged


def export_metrics_manifest(snapshot: PipelineMetricsSnapshot) -> Dict[str, Any]:
    validate_metrics_snapshot(snapshot)
    snapshot.status = METRIC_EXPORTED
    return snapshot.to_dict()


class PipelineMetricsCollector:
    """Small collector object for incremental runtime metric collection."""

    def __init__(self, metrics_id: str = "pipeline") -> None:
        self.snapshot = create_metrics_snapshot(metrics_id)

    def record(self, name: str, value: Any = 1, **metadata: Any) -> PipelineMetricRecord:
        return self.snapshot.add_record({"name": name, "value": value, "metadata": metadata})

    def collect_lifecycle(self, result_or_state: Any) -> PipelineMetricsSnapshot:
        lifecycle_snapshot = collect_lifecycle_metrics(result_or_state, metrics_id=self.snapshot.metrics_id)
        self.snapshot = merge_metrics_snapshots(self.snapshot.metrics_id, [self.snapshot, lifecycle_snapshot])
        return self.snapshot

    def manifest(self) -> Dict[str, Any]:
        return export_metrics_manifest(self.snapshot)
