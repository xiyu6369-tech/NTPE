"""NTPE 1.0 Beta Stage-09.0 Workflow Core test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflow import WorkflowCore, WorkflowContext, WorkflowDefinition, WORKFLOW_STAGE  # noqa: E402
from integration import EventBus, ServiceContainer, build_freeze_manifest, validate_freeze_manifest  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    print("NTPE 1.0 Beta Stage-09.0 Workflow Core Test")
    print("=" * 72)

    bus = EventBus()
    container = ServiceContainer(metadata={"stage": "09.0"})
    container.register_instance("translator", lambda text: f"translated:{text}")

    core = WorkflowCore(event_bus=bus, service_container=container, metadata={"stage": "09.0"})
    workflow = core.create_workflow("demo", purpose="workflow-core")

    def load(context, payload, services):
        return payload.get("text", "")

    def translate(context, payload, services):
        translator = services.resolve("translator")
        return translator(context.get("load"))

    workflow.add_step("load", load)
    workflow.add_step("translate", translate, depends_on=["load"])

    result = core.execute("demo", context=WorkflowContext(session_id="stage-09.0"), text="hello")
    manifest = core.manifest()
    freeze = validate_freeze_manifest(build_freeze_manifest({"stage": "09.0"}))

    check("Workflow Core", manifest["stage"] == WORKFLOW_STAGE and manifest["foundation_status"] == "frozen")
    check("Workflow Definition", isinstance(workflow, WorkflowDefinition) and len(workflow.steps) == 2)
    check("Workflow Registry", core.registry.get("demo") is workflow and "demo" in core.registry.names())
    check("Workflow Context", result.outputs["load"] == "hello")
    check("Step Dependency", result.outputs["translate"] == "translated:hello")
    check("Workflow Execution", result.ok and result.status.value == "completed")
    check("Event Bus Bridge", manifest["bridges"]["event_bus_attached"] is True and len(bus.history) >= 4)
    check("Service Container Bridge", manifest["bridges"]["service_container_attached"] is True and container.resolve("translator")("ok") == "translated:ok")
    check("Integration Freeze", freeze.ok and freeze.status == "frozen")
    check("Backward Compatible", manifest["additive_only"] is True and manifest["integration_status"] == "frozen")

    print("PASS")


if __name__ == "__main__":
    main()
