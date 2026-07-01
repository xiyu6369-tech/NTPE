from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.pipeline.stage_registry import create_stage_registry
from core.pipeline.dependency_resolver import resolve_stage_dependencies
from core.pipeline.scheduler import schedule_pipeline
from core.pipeline.lifecycle_manager import (
    LIFECYCLE_CLEANED,
    LIFECYCLE_COMPLETED,
    LIFECYCLE_FAILED,
    LIFECYCLE_INITIALIZED,
    LIFECYCLE_STOPPED,
    PipelineLifecycleEvent,
    create_lifecycle_manager,
    create_lifecycle_state,
    normalize_lifecycle_event,
    run_pipeline_lifecycle,
    validate_lifecycle_state,
)
from adapters.pipeline_lifecycle_adapter import (
    adapter_export_lifecycle_manifest,
    adapter_lifecycle_event,
    adapter_run_lifecycle,
    adapter_validate_lifecycle_state,
    build_pipeline_lifecycle_adapter,
)


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"{label:<28} PASS")


def main() -> None:
    print("NTPE Foundation-05.4 Pipeline Lifecycle Manager Test")
    print("====================================================")

    check("Legacy Event", normalize_lifecycle_event("legacy").type == "legacy")
    event = PipelineLifecycleEvent(type="x", status="created")
    check("Event Created", event.to_dict()["type"] == "x")

    state = create_lifecycle_state("test")
    check("State Created", state.lifecycle_id == "test")
    check("Validate State", validate_lifecycle_state(state) is True)

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

    plan = resolve_stage_dependencies(registry)
    check("Plan Ready", plan.valid is True)

    schedule = schedule_pipeline(registry)
    check("Schedule Ready", schedule.valid is True)

    manager = create_lifecycle_manager(schedule, lifecycle_id="life")
    check("Manager Created", manager.state.lifecycle_id == "life")

    init_state = manager.initialize(payload={"source": "text"})
    check("Lifecycle Initialized", init_state.status == LIFECYCLE_INITIALIZED)
    check("Init Counter", init_state.counters["initialized"] == 1)

    result = manager.start(payload={"source": "text"})
    check("Lifecycle Completed", result.status == LIFECYCLE_COMPLETED)
    check("Result OK", result.ok is True)
    check("Output Context", result.output["context"] is True)
    check("Output Quality", result.output["quality"] == "pass")
    check("Stage Counter", manager.state.counters["stages_completed"] == 3)
    check("Lifecycle Events", len(manager.state.events) >= 8)

    manifest = manager.export_manifest()
    check("Manifest Created", manifest["schema"] == "ntpe.pipeline.lifecycle_manager.v1")
    check("Manifest State", manifest["state"]["status"] == LIFECYCLE_COMPLETED)

    cleaned = manager.cleanup()
    check("Lifecycle Cleaned", cleaned.status == LIFECYCLE_CLEANED)

    stop_registry = create_stage_registry([
        {"name": "only", "handler": lambda value: value},
    ])
    stop_manager = create_lifecycle_manager(stop_registry, lifecycle_id="stop")
    stop_manager.initialize()
    stop_manager.request_stop("manual")
    stopped = stop_manager.start(payload={"x": 1})
    check("Stop Requested", stopped.status == LIFECYCLE_STOPPED)
    check("Stop Counter", stop_manager.state.counters["stopped"] == 1)

    def bad_stage(value):
        raise RuntimeError("boom")

    fail_registry = create_stage_registry([
        {"name": "bad", "handler": bad_stage},
    ])
    failed = run_pipeline_lifecycle(fail_registry, payload={})
    check("Lifecycle Failed", failed.status == LIFECYCLE_FAILED)
    check("Failure Error", "boom" in failed.error)

    adapter = build_pipeline_lifecycle_adapter(schedule, lifecycle_id="adapter")
    check("Adapter Created", adapter.state.lifecycle_id == "adapter")
    adapter_result = adapter_run_lifecycle(registry, payload={"source": "adapter"})
    check("Adapter Run", adapter_result["status"] == LIFECYCLE_COMPLETED)
    check("Adapter Validate", adapter_validate_lifecycle_state(adapter.state) is True)
    check("Adapter Event", adapter_lifecycle_event({"type": "adapter", "status": "created"})["type"] == "adapter")
    check("Adapter Manifest", adapter_export_lifecycle_manifest(adapter)["schema"] == "ntpe.pipeline.lifecycle_manager.v1")

    legacy_item = normalize_lifecycle_event({"event": "old_event", "status": "created"})
    check("Backward Compatible", legacy_item.type == "old_event")

    print("PASS")


if __name__ == "__main__":
    main()
