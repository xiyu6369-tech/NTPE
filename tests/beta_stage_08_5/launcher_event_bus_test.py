"""NTPE 1.0 Beta Stage-08.5 Event Bus test."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration import (  # noqa: E402
    EVENT_BUS_STAGE,
    EVENT_BUS_VERSION,
    Event,
    EventBus,
    EventContext,
    EventDispatcher,
    EventFilter,
    EventPublisher,
    EventRegistry,
    EventSubscriber,
    ExtensionManager,
    IntegrationCore,
    PluginIntegrationManager,
    RuntimeManager,
    SDKCLIBridge,
)
from sdk import NTPEClient  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class RuntimeStub:
    version = "runtime-event-08.5"

    def execute(self, text="", **payload):
        return {"runtime": True, "text": text, "payload": payload}


class CLIStub:
    version = "cli-event-08.5"

    def execute(self, text="", **payload):
        return {"cli": True, "text": text, "payload": payload}


async def async_part(bus: EventBus, seen: list[str]) -> bool:
    async def async_listener(event: Event):
        seen.append(f"async:{event.type}")

    bus.subscribe(async_listener, name="async-listener", topic="async", event_type="event.async")
    result = await bus.publish_async("event.async", {"ok": True}, topic="async", source="sdk")
    return result.ok and result.delivered >= 1 and "async:event.async" in seen


def main() -> None:
    print("NTPE 1.0 Beta Stage-08.5 Event Bus Test")
    print("=" * 74)

    check("Event Bus Stage", "Stage-08.5" in EVENT_BUS_STAGE and EVENT_BUS_VERSION == "0.8.5")

    runtime = RuntimeStub()
    sdk = NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)})
    cli = CLIStub()
    plugin_manager = PluginIntegrationManager()
    extension_manager = ExtensionManager(runtime=runtime, sdk=sdk, cli=cli, plugin_manager=plugin_manager)
    context = EventContext(source="integration-test", topic="ntpe", runtime=runtime, sdk=sdk, cli=cli, plugin_manager=plugin_manager, extension_manager=extension_manager)
    bus = EventBus(context=context)
    check("Event Bus Created", bus.manifest()["stage"] == EVENT_BUS_STAGE and bus.bridge_status()["runtime_attached"] is True)

    seen: list[str] = []
    bus.subscribe(lambda event: seen.append(f"general:{event.type}"), name="general", priority=1)
    bus.subscribe(lambda event: seen.append(f"sdk:{event.payload['value']}"), name="sdk-sub", topic="sdk", event_type="sdk.translation.completed", source="sdk", priority=5)
    result = bus.publish("sdk.translation.completed", {"value": "ok"}, topic="sdk", source="sdk", priority=10)
    check("Event Publish", result.ok and result.delivered == 2)
    check("Event Subscribe", "sdk:ok" in seen and "general:sdk.translation.completed" in seen)

    registry = EventRegistry()
    registry.register(lambda event: seen.append("registry"), name="registry-sub", topic="runtime")
    dispatcher = EventDispatcher(registry)
    dispatch_result = dispatcher.dispatch(Event("runtime.started", topic="runtime", source="runtime"))
    check("Event Dispatch", dispatch_result.ok and dispatch_result.delivered == 1 and "registry" in seen)

    publisher = EventPublisher(bus, source="cli", topic="cli")
    route = publisher.publish("cli.command.completed", {"command": "translate"})
    check("Event Routing", route.ok and bus.history[-1]["event"]["source"] == "cli")

    filtered = bus.filter_history(EventFilter(topics=["sdk"], sources=["sdk"], min_priority=1))
    check("Event Filtering", len(filtered) == 1 and filtered[0]["event"]["type"] == "sdk.translation.completed")

    subscriber = EventSubscriber(lambda event: seen.append("extension-event"), name="extension-sub", topic="extension", event_type="extension.enabled")
    subscriber.register(bus)
    extension_result = bus.publish("extension.enabled", {"name": "demo"}, topic="extension", source="extension")
    check("Extension Events", extension_result.ok and "extension-event" in seen)

    runtime_result = bus.publish("runtime.completed", {"runtime": True}, topic="runtime", source="runtime")
    sdk_result = bus.publish("sdk.completed", {"sdk": True}, topic="sdk", source="sdk")
    cli_result = bus.publish("cli.completed", {"cli": True}, topic="cli", source="cli")
    plugin_result = bus.publish("plugin.completed", {"plugin": True}, topic="plugin", source="plugin")
    check("Runtime Events", runtime_result.ok)
    check("SDK Events", sdk_result.ok)
    check("CLI Events", cli_result.ok)
    check("Plugin Events", plugin_result.ok)

    async_ok = asyncio.run(async_part(bus, seen))
    check("Async Event Dispatch", async_ok)

    core = IntegrationCore(metadata={"stage": "08.5"})
    core.bridge_runtime(runtime)
    core.bridge_sdk(sdk)
    core.bridge_plugin_manager(plugin_manager)
    core.register_component("event_bus", "event_bus", bus, version=bus.version)
    invoked = core.invoke("event_bus", "publish", "core.event", {"core": True}, topic="core", source="integration-core")
    check("Integration Core Events", invoked.ok and invoked.data["value"].ok)

    bridge = SDKCLIBridge(configuration={"stage": "08.5"})
    bridge.register_sdk(sdk)
    bridge.register_cli(cli)
    bridge.register_runtime(runtime)
    check("Bridge Compatible", bridge.manifest()["registry"]["count"] == 3)
    check("Foundation Freeze", bus.manifest()["foundation_status"] == "frozen")
    check("Backward Compatible", sdk.translate_text("compat").ok)

    print("PASS")


if __name__ == "__main__":
    main()
