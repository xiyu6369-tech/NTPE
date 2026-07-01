import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.pipeline.stage_registry import create_stage_registry
from core.pipeline.dependency_resolver import resolve_stage_dependencies
from core.pipeline.scheduler import (
    SCHEDULE_ITEM_BLOCKED,
    SCHEDULE_ITEM_READY,
    PipelineSchedule,
    create_pipeline_scheduler,
    normalize_schedule_item,
    schedule_pipeline,
    validate_schedule,
)
from adapters.pipeline_scheduler_adapter import (
    adapter_export_schedule_manifest,
    adapter_schedule_item,
    adapter_schedule_pipeline,
    adapter_validate_schedule,
    build_pipeline_scheduler_adapter,
)


def ok(label):
    print(f"{label:<25} PASS")


def main():
    print("NTPE Foundation-05.3 Pipeline Scheduler Test")
    print("=" * 49)

    legacy = normalize_schedule_item("context@1.0.0")
    assert legacy.stage_id == "context@1.0.0"
    ok("Legacy Item")

    registry = create_stage_registry([
        {"name": "context", "priority": 10},
        {"name": "prompt", "priority": 20, "dependencies": ["context"]},
        {"name": "quality", "priority": 30, "dependencies": ["prompt"]},
    ])
    ok("Registry Ready")

    plan = resolve_stage_dependencies(registry)
    assert list(plan.ordered_stage_ids) == ["context@1.0.0", "prompt@1.0.0", "quality@1.0.0"]
    ok("Plan Ready")

    scheduler = create_pipeline_scheduler(registry)
    assert scheduler is not None
    ok("Scheduler Created")

    schedule = scheduler.build_schedule(plan)
    assert isinstance(schedule, PipelineSchedule)
    ok("Schedule Created")

    assert validate_schedule(schedule)
    ok("Validate Schedule")

    assert schedule.valid is True
    ok("Schedule Valid")

    assert list(schedule.ordered_stage_ids) == list(plan.ordered_stage_ids)
    ok("Schedule Order")

    assert schedule.items[0].status == SCHEDULE_ITEM_READY
    ok("Item Ready")

    assert schedule.items[0].index == 0
    ok("Item Index")

    assert schedule.items[0].stage.name == "context"
    ok("Item Stage")

    manifest = scheduler.export_manifest(schedule)
    assert manifest["schema"] == "ntpe.pipeline.scheduler.v1"
    ok("Manifest Created")

    assert manifest["schedule"]["items"][1]["stage_id"] == "prompt@1.0.0"
    ok("Manifest Item")

    assert len(scheduler.events) >= 3
    ok("Scheduler Events")

    loose_schedule = schedule_pipeline(registry, strict=True)
    assert loose_schedule.valid is True
    ok("Schedule Helper")

    bad_registry = create_stage_registry([
        {"name": "context", "priority": 10},
        {"name": "prompt", "priority": 20, "dependencies": ["missing"]},
    ])
    bad_plan = resolve_stage_dependencies(bad_registry, strict=True)
    bad_schedule = create_pipeline_scheduler(bad_registry).build_schedule(bad_plan, strict=True)
    assert bad_schedule.valid is False
    ok("Blocked Detected")

    assert bad_schedule.items[0].status == SCHEDULE_ITEM_BLOCKED
    ok("Blocked Item")

    relaxed_schedule = create_pipeline_scheduler(bad_registry).build_schedule(bad_plan, strict=False)
    assert relaxed_schedule.items[0].status == SCHEDULE_ITEM_READY
    ok("Loose Schedule")

    registry.disable("prompt")
    disabled_plan = resolve_stage_dependencies(registry, enabled_only=False, strict=False)
    disabled_schedule = create_pipeline_scheduler(registry).build_schedule(disabled_plan, strict=False)
    assert "prompt@1.0.0" in disabled_schedule.skipped
    ok("Skipped Detected")

    adapter = build_pipeline_scheduler_adapter(registry)
    assert adapter is not None
    ok("Adapter Created")

    adapter_result = adapter_schedule_pipeline(registry, strict=False)
    assert adapter_result["schema"] == "ntpe.pipeline.schedule.v1"
    ok("Adapter Schedule")

    assert adapter_schedule_item("context@1.0.0")["stage_id"] == "context@1.0.0"
    ok("Adapter Item")

    assert adapter_validate_schedule(schedule)
    ok("Adapter Validate")

    assert adapter_export_schedule_manifest(scheduler, schedule)["schema"] == "ntpe.pipeline.scheduler.v1"
    ok("Adapter Manifest")

    assert normalize_schedule_item({"stage_id": "legacy@1.0.0", "index": 7}).index == 7
    ok("Backward Compatible")

    print("PASS")


if __name__ == "__main__":
    main()
