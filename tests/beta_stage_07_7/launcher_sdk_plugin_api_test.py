"""NTPE 1.0 Beta Stage-07.7 SDK Plugin API test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdk import (  # noqa: E402
    SDK_PLUGIN_STAGE,
    SDK_PLUGIN_VERSION,
    SDK_CONFIG_STAGE,
    SDKPlugin,
    SDKPluginContext,
    SDKPluginLoader,
    SDKPluginManager,
    SDKPluginRegistry,
    PluginManifest,
    PluginResult,
    build_sdk_plugin_manifest,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class UppercasePlugin(SDKPlugin):
    name = "uppercase"
    version = "1.0.0"
    capabilities = ["translation.postprocess", "text.transform"]

    def execute(self, context=None, **kwargs):
        text = kwargs.get("text", "")
        if context:
            context.emit("uppercase.executed", input=text)
        return PluginResult(self.manifest.name, output=str(text).upper(), metadata={"executed": True})


class BrokenPlugin(SDKPlugin):
    name = "broken"
    version = "1.0.0"
    capabilities = ["error.test"]

    def execute(self, context=None, **kwargs):
        raise RuntimeError("expected plugin failure")


def main() -> None:
    print("NTPE 1.0 Beta Stage-07.7 SDK Plugin API Test")
    print("=" * 64)

    context = SDKPluginContext(payload={"source": "sdk"}, metadata={"stage": "07.7"})
    event = context.emit("context.created", ok=True)
    check("Plugin Context", event["type"] == "context.created" and len(context.events) == 1)

    manifest = PluginManifest(name="manifest-plugin", version="1.2.3", capabilities=["manifest.test"])
    base_plugin = SDKPlugin(manifest=manifest)
    check("SDK Plugin Created", base_plugin.descriptor().name == "manifest-plugin")

    registry = SDKPluginRegistry()
    plugin = UppercasePlugin()
    registry.register(plugin)
    check("Plugin Registry", registry.get("uppercase") is plugin and "uppercase" in registry.names())

    loader = SDKPluginLoader()
    loaded = loader.from_manifest({"name": "loaded-plugin", "version": "0.1.0", "capabilities": ["loaded"]})
    check("Plugin Loader", loaded.manifest.name == "loaded-plugin" and loaded.descriptor().version == "0.1.0")

    manager = SDKPluginManager(context=context)
    manager.register(plugin)
    manager.register(BrokenPlugin(), replace=True)
    load_result = plugin.load(context)
    init_result = manager.initialize("uppercase")
    exec_result = manager.execute("uppercase", text="ntpe")
    unload_result = manager.unload("uppercase")
    check("Plugin Lifecycle", load_result.ok and init_result.ok and exec_result.output == "NTPE" and unload_result.ok)

    discovered = manager.discover("text.transform")
    check("Plugin Discovery", len(discovered) == 1 and discovered[0].name == "uppercase")

    bridge = manager.runtime_bridge()
    check("Runtime Plugin Bridge", bridge["stage"] == "Stage-07.7" and bridge["payload"]["source"] == "sdk")

    error_result = manager.execute("broken")
    check("Plugin Error Isolation", error_result.status == "error" and error_result.metadata["isolated"] is True)

    manifest_data = build_sdk_plugin_manifest({"config_stage": SDK_CONFIG_STAGE})
    check("SDK Plugin Manifest", manifest_data["version"] == SDK_PLUGIN_VERSION and "SDKPluginManager" in manifest_data["components"])
    check("Backward Compatible", manifest_data["backward_compatible"] is True and "Stage-07.6" in manifest_data["sdk_config_compatibility"] and "Stage-07.7" in SDK_PLUGIN_STAGE)

    print("PASS")


if __name__ == "__main__":
    main()
