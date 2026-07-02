"""NTPE 1.0 Beta Stage-08.0 Integration Core test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration import (  # noqa: E402
    INTEGRATION_STAGE,
    INTEGRATION_VERSION,
    IntegrationComponent,
    IntegrationContext,
    IntegrationCore,
    IntegrationRegistry,
    build_integration_manifest,
    create_integration_core,
)
from sdk import NTPEClient, SDKPluginManager  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class RuntimeStub:
    version = "runtime-stub"

    def status(self):
        return {"status": "ready"}


def main() -> None:
    print("NTPE 1.0 Beta Stage-08.0 Integration Core Test")
    print("=" * 72)

    manifest = build_integration_manifest({"test": True})
    check("Integration Manifest", manifest["version"] == INTEGRATION_VERSION and manifest["foundation_status"] == "frozen")
    check("Integration Stage", "Stage-08.0" in INTEGRATION_STAGE and manifest["compatibility"]["sdk_stage_07"] is True)

    registry = IntegrationRegistry()
    component = registry.register(IntegrationComponent(name="runtime", kind="runtime", version="1.0"))
    check("Integration Registry", registry.require("runtime") is component and registry.manifest()["count"] == 1)

    context = IntegrationContext(operation="test.operation")
    child = context.child("test.child", value=1)
    check("Integration Context", child.metadata["parent_correlation_id"] == context.correlation_id and child.operation == "test.child")

    client = NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)})
    plugin_manager = SDKPluginManager()
    core = create_integration_core(metadata={"stage": "08.0"})
    core.bridge_sdk(client)
    core.bridge_runtime(RuntimeStub())
    core.bridge_plugin_manager(plugin_manager)
    check("Integration Core Created", isinstance(core, IntegrationCore) and len(core.registry.names()) == 3)

    result = core.invoke("sdk", "translate_text", "integration-ok")
    check("SDK Bridge Invoke", result.ok and result.data["value"].ok and result.data["value"].text == "integration-ok")

    runtime_result = core.invoke("runtime", "status")
    check("Runtime Bridge Invoke", runtime_result.ok and runtime_result.data["value"]["status"] == "ready")

    health = core.health()
    check("Integration Health", health.ok and health.data["registry"]["count"] == 3)

    core_manifest = core.manifest()
    check("Runtime Shared", core_manifest["compatibility"]["runtime_shared"] is True)
    check("Backward Compatible", client.translate_text("stage-08.0").ok and client.version.startswith("0.7"))
    check("Event Recorded", len(core_manifest["events"]) >= 3)

    print("PASS")


if __name__ == "__main__":
    main()
