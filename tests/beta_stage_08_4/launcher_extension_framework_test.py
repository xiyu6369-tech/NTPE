"""NTPE 1.0 Beta Stage-08.4 Extension Framework test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration import (  # noqa: E402
    EXTENSION_FRAMEWORK_STAGE,
    EXTENSION_FRAMEWORK_VERSION,
    ExtensionCommand,
    ExtensionContext,
    ExtensionDispatcher,
    ExtensionEventBus,
    ExtensionManager,
    ExtensionManifest,
    ExtensionRegistry,
    IntegrationCore,
    PluginIntegrationManager,
    build_extension_manifest,
)
from sdk import NTPEClient  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class RuntimeStub:
    version = "runtime-extension-08.4"

    def execute(self, text="", **payload):
        return {"runtime": True, "text": text, "payload": payload}


class CLIStub:
    version = "cli-extension-08.4"

    def execute(self, text="", **payload):
        return {"cli": True, "text": text, "payload": payload}


class EchoExtension:
    name = "echo-extension"
    version = "1.0.0"
    capabilities = ["translate", "echo"]
    kind = "extension"

    def __init__(self):
        self.loaded = False
        self.initialized = False
        self.enabled = False

    def load(self, context=None, **payload):
        self.loaded = True
        return {"loaded": True, "runtime": getattr(context, "runtime", None) is not None}

    def initialize(self, context=None, **payload):
        self.initialized = True
        return {"initialized": True, "sdk": getattr(context, "sdk", None) is not None}

    def enable(self, context=None, **payload):
        self.enabled = True
        return {"enabled": True}

    def disable(self, context=None, **payload):
        self.enabled = False
        return {"enabled": False}

    def execute(self, context=None, **payload):
        return {"echo": payload.get("text", ""), "cli": getattr(context, "cli", None) is not None, "plugin": getattr(context, "plugin_manager", None) is not None}

    def unload(self, context=None, **payload):
        self.loaded = False
        self.initialized = False
        return {"unloaded": True}


def main() -> None:
    print("NTPE 1.0 Beta Stage-08.4 Extension Framework Test")
    print("=" * 74)

    check("Extension Framework Stage", "Stage-08.4" in EXTENSION_FRAMEWORK_STAGE and EXTENSION_FRAMEWORK_VERSION == "0.8.4")

    manifest = build_extension_manifest("echo-extension", version="1.0.0", capabilities=["translate", "echo"], entrypoint="tests.beta_stage_08_4.launcher_extension_framework_test:EchoExtension")
    check("Extension Manifest", isinstance(manifest, ExtensionManifest) and manifest.validate() and manifest.name == "echo-extension")

    events = ExtensionEventBus()
    seen = []
    events.subscribe(lambda event: seen.append(event.to_dict()))
    manager = ExtensionManager(events=events, runtime=RuntimeStub(), sdk=NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)}), cli=CLIStub(), plugin_manager=PluginIntegrationManager(), config={"language": "zh-TW"})
    name = manager.register(EchoExtension(), manifest=manifest, replace=True, metadata={"stage": "08.4"})
    check("Extension Registry", name == "echo-extension" and manager.registry.manifest()["count"] == 1)

    registry = ExtensionRegistry()
    registry.register(EchoExtension(), manifest=manifest, replace=True)
    dispatcher = ExtensionDispatcher(registry)
    context = ExtensionContext(operation="extension.dispatch", extension_name="echo-extension", runtime=RuntimeStub(), sdk=manager.sdk, cli=CLIStub(), plugin_manager=manager.plugin_manager)
    dispatched = dispatcher.dispatch(ExtensionCommand("echo-extension", "execute", {"text": "dispatch-ok"}), context)
    check("Extension Dispatcher", dispatched.ok and dispatched.value["echo"] == "dispatch-ok" and dispatched.value["cli"] is True)

    lifecycle = manager.lifecycle("echo-extension")
    check("Extension Lifecycle", lifecycle["load"].ok and lifecycle["initialize"].ok and lifecycle["enable"].ok)

    executed = manager.execute("echo-extension", text="manager-ok")
    disabled = manager.disable("echo-extension")
    unloaded = manager.unload("echo-extension")
    check("Extension Manager", executed.ok and executed.value["echo"] == "manager-ok" and disabled.ok and unloaded.ok)
    check("Extension Events", len(seen) >= 6 and manager.manifest()["events"]["count"] >= 6)

    discovered = manager.discover("translate")
    check("Extension Discovery", len(discovered) == 1 and discovered[0]["name"] == "echo-extension")

    bridge = manager.bridge_status()
    check("Runtime Bridge", bridge["runtime_attached"] is True)
    check("SDK Bridge", bridge["sdk_attached"] is True)
    check("CLI Bridge", bridge["cli_attached"] is True)
    check("Plugin Bridge", bridge["plugin_manager_attached"] is True)

    core = IntegrationCore(metadata={"stage": "08.4"})
    core.bridge_runtime(RuntimeStub())
    core.bridge_sdk(NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)}))
    core.bridge_plugin_manager(manager.plugin_manager)
    core.register_component("extension_manager", "extension", manager, version=manager.version)
    invoked = core.invoke("extension_manager", "execute", "echo-extension", text="core-ok")
    check("Extension Framework", invoked.ok and invoked.data["value"].value["echo"] == "core-ok")
    check("Foundation Freeze", core.manifest()["foundation_status"] == "frozen")
    check("Backward Compatible", NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)}).translate_text("compat").ok)

    print("PASS")


if __name__ == "__main__":
    main()
