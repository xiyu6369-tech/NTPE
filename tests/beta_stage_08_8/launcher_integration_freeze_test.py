"""NTPE 1.0 Beta Stage-08.8 Integration Freeze test."""
from __future__ import annotations

import sys
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration import (  # noqa: E402
    INTEGRATION_FREEZE_VERSION,
    INTEGRATION_FREEZE_STATUS,
    IntegrationCore,
    RuntimeManager,
    SDKCLIBridge,
    PluginIntegrationManager,
    ExtensionManager,
    EventBus,
    ServiceContainer,
    build_freeze_manifest,
    build_integration_contract,
    build_compatibility_matrix,
    build_version_manifest,
    validate_freeze_manifest,
    write_freeze_artifacts,
    load_json,
    freeze_is_compatible,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class RuntimeStub:
    version = "runtime-freeze-08.8"

    def execute(self, text="", **payload):
        return {"runtime": True, "text": text, "payload": payload}


class CLIStub:
    version = "cli-freeze-08.8"

    def execute(self, text="", **payload):
        return {"cli": True, "text": text, "payload": payload}


def main() -> None:
    print("NTPE 1.0 Beta Stage-08.8 Integration Freeze Test")
    print("=" * 78)

    manifest = build_freeze_manifest({"stage": "08.8"})
    result = validate_freeze_manifest(manifest)
    contract = build_integration_contract()
    matrix = build_compatibility_matrix()
    version = build_version_manifest()

    check("Integration Freeze", result.ok and result.status == INTEGRATION_FREEZE_STATUS)
    check("Integration Contract", contract["status"] == "frozen" and len(contract["frozen_surfaces"]) >= 7)
    check("Compatibility Matrix", freeze_is_compatible(matrix))
    check("Version Manifest", version["version"] == INTEGRATION_FREEZE_VERSION and version["status"] == "frozen")

    runtime = RuntimeStub()
    cli = CLIStub()
    bridge = SDKCLIBridge(configuration={"stage": "08.8"})
    bridge.register_runtime(runtime)
    bridge.register_cli(cli)
    plugin_manager = PluginIntegrationManager()
    extension_manager = ExtensionManager(runtime=runtime, cli=cli, plugin_manager=plugin_manager)
    bus = EventBus()
    container = ServiceContainer(metadata={"stage": "08.8"})
    container.bridge_runtime(runtime).bridge_cli(cli).bridge_plugin_manager(plugin_manager).bridge_extension_manager(extension_manager)
    container.register_instance("event_bus", bus)
    container.register_instance("sdk_cli_bridge", bridge)

    core = IntegrationCore(metadata={"stage": "08.8", "freeze": True})
    core.register_component("runtime", "runtime_manager", RuntimeManager(), version="08.1")
    core.register_component("bridge", "sdk_cli_bridge", bridge, version="08.2")
    core.register_component("plugin", "plugin_manager", plugin_manager, version="08.3")
    core.register_component("extension", "extension_manager", extension_manager, version="08.4")
    core.register_component("event_bus", "event_bus", bus, version="08.5")
    core.register_component("service_container", "service_container", container, version="08.6")

    check("Runtime Compatibility", core.invoke("runtime", "manifest").ok)
    check("SDK Compatibility", bridge.manifest()["stage"].startswith("NTPE 1.0 Beta Stage-08.2"))
    check("CLI Compatibility", bridge.sdk_to_cli("execute", text="ok").ok)
    check("Plugin Compatibility", plugin_manager.manifest()["stage"].startswith("NTPE 1.0 Beta Stage-08.3"))
    check("Extension Compatibility", extension_manager.manifest()["bridge"]["plugin_manager_attached"] is True)
    check("Event Bus Compatibility", bus.publish("freeze.ok", {"ok": True}, topic="freeze").ok)
    check("Service Compatibility", container.resolve("runtime") is runtime and container.validate()["ok"] is True)

    with tempfile.TemporaryDirectory() as tmp:
        written = write_freeze_artifacts(tmp, {"stage": "08.8"})
        loaded_manifest = load_json(written["freeze_manifest.json"])
        loaded_matrix = load_json(written["compatibility_matrix.json"])
        check("Freeze Artifacts", len(written) == 4 and validate_freeze_manifest(loaded_manifest).ok)
        check("Artifact Compatibility", freeze_is_compatible(loaded_matrix))

    check("Foundation Freeze", manifest["foundation_status"] == "frozen")
    check("Backward Compatible", manifest["additive_only"] is True and contract["rules"]["backward_compatible"] is True)

    print("PASS")


if __name__ == "__main__":
    main()
