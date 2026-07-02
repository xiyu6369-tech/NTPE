"""NTPE 1.0 Beta Stage-08.3 Plugin Integration test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration import (  # noqa: E402
    IntegrationCore,
    PluginCommand,
    PluginDispatcher,
    PluginEventBus,
    PluginIntegrationBridge,
    PluginIntegrationContext,
    PluginIntegrationManager,
    PluginIntegrationRegistry,
    PLUGIN_INTEGRATION_STAGE,
    PLUGIN_INTEGRATION_VERSION,
)
from sdk import NTPEClient, SDKPlugin, SDKPluginManager  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class EchoPlugin(SDKPlugin):
    name = "echo-plugin"
    version = "1.0.0"
    capabilities = ["translate", "echo"]

    def execute(self, context=None, **kwargs):
        result = super().execute(context, **kwargs)
        result.output = {"echo": kwargs.get("text", ""), "runtime": getattr(context, "runtime", None) is not None}
        return result


class CLIAdapterStub:
    version = "cli-plugin-08.3"

    def execute(self, text="", **payload):
        return {"cli": True, "text": text, "payload": payload}


class RuntimeStub:
    version = "runtime-plugin-08.3"

    def execute(self, text="", **payload):
        return {"runtime": True, "text": text, "payload": payload}


def main() -> None:
    print("NTPE 1.0 Beta Stage-08.3 Plugin Integration Test")
    print("=" * 72)

    check("Plugin Integration Stage", "Stage-08.3" in PLUGIN_INTEGRATION_STAGE and PLUGIN_INTEGRATION_VERSION == "0.8.3")

    events = PluginEventBus()
    seen = []
    events.subscribe(lambda event: seen.append(event.to_dict()))
    bridge = PluginIntegrationBridge(events=events, runtime=RuntimeStub(), sdk=NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)}), cli=CLIAdapterStub(), config={"language": "zh-TW"})
    plugin_name = bridge.register(EchoPlugin(), source="sdk", replace=True, metadata={"stage": "08.3"})
    check("Plugin Bridge", plugin_name == "echo-plugin" and bridge.runtime_bridge()["runtime_attached"] is True)

    registry = bridge.registry
    check("Plugin Registry", registry.names() == ["echo-plugin"] and registry.manifest()["count"] == 1)

    dispatcher = PluginDispatcher(registry)
    context = PluginIntegrationContext(operation="plugin.dispatch", plugin_name="echo-plugin", runtime=bridge.runtime, sdk=bridge.sdk, cli=bridge.cli, config=bridge.config)
    dispatched = dispatcher.dispatch(PluginCommand("echo-plugin", "execute", {"text": "dispatch-ok"}), context)
    check("Plugin Dispatcher", dispatched.ok and dispatched.value.ok and dispatched.value.output["echo"] == "dispatch-ok")

    loaded = bridge.load("echo-plugin")
    initialized = bridge.initialize("echo-plugin")
    executed = bridge.execute("echo-plugin", text="runtime-ok")
    unloaded = bridge.unload("echo-plugin")
    check("Plugin Lifecycle", loaded.ok and initialized.ok and executed.ok and unloaded.ok)
    check("Plugin Events", len(seen) >= 5 and bridge.manifest()["events"]["count"] >= 5)

    discovered = bridge.discover("translate")
    check("Plugin Discovery", len(discovered) == 1 and discovered[0]["name"] == "echo-plugin")

    manager = PluginIntegrationManager(bridge=bridge)
    manager_manifest = manager.manifest()
    check("Plugin Manager", manager_manifest["manager_version"] == "0.8.3" and manager_manifest["registry"]["count"] == 1)

    sdk_manager = SDKPluginManager()
    sdk_manager.register(EchoPlugin(), replace=True)
    sdk_result = sdk_manager.execute("echo-plugin", text="sdk-ok")
    check("SDK Integration", sdk_result.ok and sdk_result.output["echo"] == "sdk-ok")

    cli_result = bridge.cli.execute(text="cli-ok")
    runtime_result = bridge.runtime.execute(text="runtime-direct")
    check("CLI Integration", cli_result["cli"] is True and cli_result["text"] == "cli-ok")
    check("Runtime Integration", runtime_result["runtime"] is True)

    core = IntegrationCore(metadata={"stage": "08.3"})
    core.bridge_runtime(RuntimeStub())
    core.bridge_sdk(NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)}))
    core.bridge_plugin_manager(manager)
    core.register_component("plugin_bridge", "plugin", bridge, version=bridge.version)
    invoked = core.invoke("plugin_bridge", "execute", "echo-plugin", text="core-plugin")
    check("Plugin Integration", invoked.ok and invoked.data["value"].ok)
    check("Foundation Freeze", core.manifest()["foundation_status"] == "frozen")
    check("Backward Compatible", NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)}).translate_text("compat").ok)

    print("PASS")


if __name__ == "__main__":
    main()
