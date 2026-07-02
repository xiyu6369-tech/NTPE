"""NTPE 1.0 Beta Stage-08.6 Service Container test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration import (  # noqa: E402
    SERVICE_CONTAINER_STAGE,
    SERVICE_CONTAINER_VERSION,
    DependencyGraph,
    EventBus,
    ExtensionManager,
    IntegrationCore,
    PluginIntegrationManager,
    SDKCLIBridge,
    ServiceContainer,
    ServiceLifetime,
    ServiceProvider,
    ServiceRegistry,
    ServiceResolver,
    ServiceScope,
)
from sdk import NTPEClient  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class RuntimeStub:
    version = "runtime-service-08.6"

    def execute(self, text="", **payload):
        return {"runtime": True, "text": text, "payload": payload}


class CLIStub:
    version = "cli-service-08.6"

    def execute(self, text="", **payload):
        return {"cli": True, "text": text, "payload": payload}


def main() -> None:
    print("NTPE 1.0 Beta Stage-08.6 Service Container Test")
    print("=" * 78)

    check("Service Container Stage", "Stage-08.6" in SERVICE_CONTAINER_STAGE and SERVICE_CONTAINER_VERSION == "0.8.6")

    container = ServiceContainer(metadata={"stage": "08.6"})
    check("Service Container", container.manifest()["stage"] == SERVICE_CONTAINER_STAGE)

    registry = ServiceRegistry()
    registry.register_instance("config", {"lang": "zh-TW"})
    registry.register("translator", lambda config: f"translator:{config['lang']}", lifetime=ServiceLifetime.SINGLETON, dependencies=["config"])
    resolver = ServiceResolver(registry)
    first = resolver.resolve("translator")
    second = resolver.resolve("translator")
    check("Service Registry", registry.has("config") and registry.has("translator"))
    check("Dependency Injection", first == "translator:zh-TW")
    check("Service Resolver", first is second)

    scoped_registry = ServiceRegistry()
    scoped_registry.register("session", lambda: object(), lifetime=ServiceLifetime.SCOPED)
    scoped_resolver = ServiceResolver(scoped_registry)
    scope_a = ServiceScope("a")
    scope_b = ServiceScope("b")
    a1 = scoped_resolver.resolve("session", scope=scope_a)
    a2 = scoped_resolver.resolve("session", scope=scope_a)
    b1 = scoped_resolver.resolve("session", scope=scope_b)
    check("Service Lifetime", a1 is a2 and a1 is not b1)

    container.register_instance("settings", {"mode": "beta"})
    container.register("factory_service", lambda settings: {"created": True, "mode": settings["mode"]}, dependencies=["settings"])
    created = container.resolve("factory_service")
    check("Factory Creation", created["created"] and created["mode"] == "beta")

    graph_result = DependencyGraph(container.registry).validate()
    check("Dependency Graph", graph_result["ok"] is True and "factory_service" in graph_result["graph"])

    runtime = RuntimeStub()
    sdk = NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)})
    cli = CLIStub()
    plugin_manager = PluginIntegrationManager()
    extension_manager = ExtensionManager(runtime=runtime, sdk=sdk, cli=cli, plugin_manager=plugin_manager)
    container.bridge_runtime(runtime).bridge_sdk(sdk).bridge_cli(cli).bridge_plugin_manager(plugin_manager).bridge_extension_manager(extension_manager)
    check("Runtime Integration", container.resolve("runtime") is runtime)
    check("SDK Integration", container.resolve("sdk") is sdk and sdk.translate_text("ok").ok)
    check("CLI Integration", container.resolve("cli") is cli)
    check("Plugin Integration", container.resolve("plugin_manager") is plugin_manager)
    check("Extension Integration", container.resolve("extension_manager") is extension_manager)

    provider = container.provider()
    scoped_provider = container.scoped_provider()
    check("Service Provider", isinstance(provider, ServiceProvider) and provider.get("runtime") is runtime and isinstance(scoped_provider.scope, ServiceScope))

    bus = EventBus()
    container.register_instance("event_bus", bus)
    event_result = container.resolve("event_bus").publish("service.ready", {"ok": True}, topic="service", source="container")
    check("Event Bus Integration", event_result.ok)

    core = IntegrationCore(metadata={"stage": "08.6"})
    core.register_component("service_container", "service_container", container, version=container.version)
    invoked = core.invoke("service_container", "resolve", "runtime")
    check("Integration Core Service", invoked.ok and invoked.data["value"] is runtime)

    bridge = SDKCLIBridge(configuration={"stage": "08.6"})
    bridge.register_sdk(sdk)
    bridge.register_cli(cli)
    bridge.register_runtime(runtime)
    container.register_instance("sdk_cli_bridge", bridge)
    check("Bridge Compatible", container.resolve("sdk_cli_bridge").manifest()["registry"]["count"] == 3)

    manifest = container.manifest()
    check("Foundation Freeze", manifest["foundation_status"] == "frozen")
    check("Backward Compatible", manifest["validation"]["ok"] is True and sdk.translate_text("compat").ok)

    print("PASS")


if __name__ == "__main__":
    main()
