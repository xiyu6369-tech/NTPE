from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.pipeline.stage_registry import create_stage_registry
from core.pipeline.lifecycle_manager import (
    LIFECYCLE_COMPLETED,
    LIFECYCLE_FAILED,
    run_pipeline_lifecycle,
)
from core.pipeline.metrics import (
    METRICS_SCHEMA,
    PipelineMetricRecord,
    PipelineMetricsCollector,
    collect_lifecycle_metrics,
    create_metrics_snapshot,
    export_metrics_manifest,
    merge_metrics_snapshots,
    normalize_metric_record,
    validate_metrics_snapshot,
)
from adapters.pipeline_metrics_adapter import (
    adapter_collect_lifecycle_metrics,
    adapter_export_metrics_manifest,
    adapter_metric_record,
    adapter_validate_metrics_snapshot,
    build_pipeline_metrics_adapter,
)


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"{label:<28} PASS")


def main() -> None:
    print("NTPE Foundation-05.5 Pipeline Metrics Test")
    print("==========================================")

    legacy = normalize_metric_record("legacy_metric")
    check("Legacy Metric", legacy.name == "legacy_metric")

    record = PipelineMetricRecord(name="x", value=2, unit="ms", category="timing")
    check("Record Created", record.to_dict()["value"] == 2)

    snapshot = create_metrics_snapshot("metrics")
    check("Snapshot Created", snapshot.metrics_id == "metrics")
    check("Validate Snapshot", validate_metrics_snapshot(snapshot) is True)

    snapshot.add_record({"name": "custom", "value": 3})
    check("Record Added", snapshot.counters["records"] == 2)

    def context_stage(value):
        data = dict(value or {})
        data["context"] = True
        return data

    def prompt_stage(value):
        data = dict(value or {})
        data["prompt"] = "ready"
        return data

    def quality_stage(value):
        data = dict(value or {})
        data["quality"] = "pass"
        return data

    registry = create_stage_registry([
        {"name": "context", "priority": 10, "handler": context_stage},
        {"name": "prompt", "priority": 20, "dependencies": ["context"], "handler": prompt_stage},
        {"name": "quality", "priority": 30, "dependencies": ["prompt"], "handler": quality_stage},
    ])
    check("Registry Ready", len(registry.list()) == 3)

    result = run_pipeline_lifecycle(registry, payload={"source": "text"}, lifecycle_id="metrics-life")
    check("Lifecycle Completed", result.status == LIFECYCLE_COMPLETED)

    metrics = collect_lifecycle_metrics(result, metrics_id="run")
    check("Metrics Collected", metrics.metadata["source"] == "lifecycle")
    check("Metrics Status", metrics.metadata["status"] == LIFECYCLE_COMPLETED)
    check("Event Counter", metrics.counters["events"] >= 8)
    check("Stage Started", metrics.counters["stages_started"] == 3)
    check("Stage Completed", metrics.counters["stages_completed"] == 3)
    check("Run Completed", metrics.counters["runs_completed"] == 1)
    check("Timing Created", "duration_seconds" in metrics.timings)
    check("Stage Status", metrics.stage_status["quality"] == "completed")

    manifest = export_metrics_manifest(metrics)
    check("Manifest Created", manifest["schema"] == METRICS_SCHEMA)
    check("Manifest Records", manifest["counters"]["records"] == len(manifest["records"]))

    def bad_stage(value):
        raise RuntimeError("boom")

    failed_registry = create_stage_registry([
        {"name": "bad", "handler": bad_stage},
    ])
    failed_result = run_pipeline_lifecycle(failed_registry, payload={}, lifecycle_id="failed")
    check("Lifecycle Failed", failed_result.status == LIFECYCLE_FAILED)

    failed_metrics = collect_lifecycle_metrics(failed_result, metrics_id="failed")
    check("Failure Counter", failed_metrics.counters["runs_failed"] == 1)
    check("Failure Stage", failed_metrics.stage_status["bad"] == "failed")

    merged = merge_metrics_snapshots("merged", [metrics, failed_metrics])
    check("Metrics Merged", merged.counters["runs_completed"] == 1)
    check("Merged Failure", merged.counters["runs_failed"] == 1)

    collector = PipelineMetricsCollector("collector")
    collector.record("manual", 5)
    collector.collect_lifecycle(result)
    check("Collector Record", collector.snapshot.counters["records"] >= 2)
    check("Collector Manifest", collector.manifest()["schema"] == METRICS_SCHEMA)

    adapter = build_pipeline_metrics_adapter("adapter")
    check("Adapter Created", adapter.snapshot.metrics_id == "adapter")
    check("Adapter Record", adapter_metric_record({"metric": "adapter_metric"})["name"] == "adapter_metric")
    adapter_metrics = adapter_collect_lifecycle_metrics(result, metrics_id="adapter-run")
    check("Adapter Collect", adapter_metrics["metadata"]["status"] == LIFECYCLE_COMPLETED)
    check("Adapter Validate", adapter_validate_metrics_snapshot(metrics) is True)
    check("Adapter Manifest", adapter_export_metrics_manifest(adapter)["schema"] == METRICS_SCHEMA)

    legacy_map = normalize_metric_record({"metric": "old", "value": 7})
    check("Backward Compatible", legacy_map.name == "old" and legacy_map.value == 7)

    print("PASS")


if __name__ == "__main__":
    main()
