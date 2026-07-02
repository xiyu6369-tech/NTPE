"""NTPE 1.0 Beta Stage-08.2 SDK-CLI Bridge test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration import (  # noqa: E402
    BRIDGE_INTEGRATION_STAGE,
    BRIDGE_INTEGRATION_VERSION,
    BridgeCommand,
    BridgeContext,
    BridgeDispatcher,
    BridgeEventBus,
    BridgeManager,
    IntegrationCore,
    SDKCLIBridge,
)
from sdk import NTPEClient  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class CLIAdapterStub:
    version = "cli-adapter-08.2"

    def __init__(self) -> None:
        self.commands = []

    def execute(self, text="", **payload):
        self.commands.append({"text": text, **payload})
        return {"cli": True, "text": text, "count": len(self.commands)}

    def status(self):
        return {"status": "ready", "commands": len(self.commands)}


class RuntimeStub:
    version = "runtime-bridge-08.2"

    def execute(self, text="", **payload):
        return {"runtime": True, "text": text, "payload": payload}

    def status(self):
        return {"status": "runtime-ready"}


def main() -> None:
    print("NTPE 1.0 Beta Stage-08.2 SDK-CLI Bridge Test")
    print("=" * 72)

    check("Bridge Stage", "Stage-08.2" in BRIDGE_INTEGRATION_STAGE and BRIDGE_INTEGRATION_VERSION == "0.8.2")

    events = BridgeEventBus()
    seen = []
    events.subscribe(lambda event: seen.append(event.to_dict()))
    bridge = SDKCLIBridge(events=events, configuration={"language": "zh-TW", "provider": "test"})
    bridge.register_sdk(NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)}))
    bridge.register_cli(CLIAdapterStub())
    bridge.register_runtime(RuntimeStub())
    check("SDK-CLI Bridge", set(bridge.registry.names()) == {"cli", "runtime", "sdk"})

    registry = bridge.registry
    check("Bridge Registry", registry.require("sdk").kind == "sdk" and registry.manifest()["count"] == 3)

    dispatcher = BridgeDispatcher(registry)
    routed = dispatcher.dispatch(BridgeCommand("cli", "execute", {"text": "dispatch-ok"}))
    check("Bridge Dispatcher", routed.ok and routed.value["text"] == "dispatch-ok")

    session = bridge.create_session("session-082", user="sdk-cli")
    context = BridgeContext(operation="bridge.test", surface="sdk", session_id=session["session_id"], configuration=bridge.shared_configuration())
    child = context.child("bridge.child", item=1)
    check("Shared Session", session["session_id"] == "session-082" and child.metadata["parent_correlation_id"] == context.correlation_id)
    check("Shared Configuration", bridge.shared_configuration()["language"] == "zh-TW")

    cli_result = bridge.sdk_to_cli("execute", text="sdk-to-cli", session_id="session-082")
    sdk_result = bridge.cli_to_sdk("translate_text", text="cli-to-sdk", session_id="session-082")
    runtime_result = bridge.route("runtime", "execute", text="runtime-ok")
    check("Command Routing", cli_result.ok and cli_result.value["cli"] is True)
    check("Event Routing", sdk_result.ok and sdk_result.value.ok and runtime_result.ok and len(seen) >= 6)
    check("Shared Runtime", runtime_result.value["runtime"] is True)

    manager = BridgeManager(bridge=bridge)
    manager_manifest = manager.manifest()
    check("Bridge Manager", manager_manifest["manager_version"] == "0.8.2" and manager_manifest["registry"]["count"] == 3)

    core = IntegrationCore(metadata={"stage": "08.2"})
    core.bridge_sdk(NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)}))
    core.bridge_runtime(RuntimeStub())
    core.bridge_plugin_manager(object())
    core.register_component("sdk_cli_bridge", "bridge", bridge, version=bridge.version)
    invoked = core.invoke("sdk_cli_bridge", "cli_to_sdk", "translate_text", text="core-bridge")
    check("SDK Integration", invoked.ok and invoked.data["value"].ok)
    check("CLI Integration", core.invoke("sdk_cli_bridge", "sdk_to_cli", "execute", text="core-cli").ok)

    manifest = bridge.manifest()
    check("Foundation Freeze", core.manifest()["foundation_status"] == "frozen")
    check("Backward Compatible", NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)}).translate_text("compat").ok and manifest["version"] == "0.8.2")

    print("PASS")


if __name__ == "__main__":
    main()
