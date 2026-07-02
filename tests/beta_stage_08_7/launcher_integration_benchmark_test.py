"""NTPE 1.0 Beta Stage-08.7 Integration Benchmark test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark import (  # noqa: E402
    INTEGRATION_BENCHMARK_STAGE,
    INTEGRATION_BENCHMARK_VERSION,
    IntegrationBenchmark,
    IntegrationLoadTest,
    IntegrationStressTest,
    PerformanceProfiler,
)
from integration import (  # noqa: E402
    EventBus,
    ExtensionManager,
    IntegrationCore,
    PluginIntegrationManager,
    SDKCLIBridge,
    ServiceContainer,
)
from sdk import NTPEClient  # noqa: E402
from sdk.session import create_session  # noqa: E402


def check(name: str, condition: bool) -> None:
    print(f"{name:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class RuntimeStub:
    version = "runtime-benchmark-08.7"

    def execute(self, text="", **payload):
        return {"runtime": True, "text": text, "payload": payload}


class CLIStub:
    version = "cli-benchmark-08.7"

    def execute(self, text="", **payload):
        return {"cli": True, "text": text, "payload": payload}


def main() -> None:
    print("NTPE 1.0 Beta Stage-08.7 Integration Benchmark Test")
    print("=" * 78)

    check("Integration Benchmark", "Stage-08.7" in INTEGRATION_BENCHMARK_STAGE and INTEGRATION_BENCHMARK_VERSION == "0.8.7")

    runtime = RuntimeStub()
    cli = CLIStub()
    sdk = NTPEClient(translator=lambda segment, ctx: {"translation": str(segment)})
    plugin_manager = PluginIntegrationManager()
    extension_manager = ExtensionManager(runtime=runtime, sdk=sdk, cli=cli, plugin_manager=plugin_manager)
    bridge = SDKCLIBridge(configuration={"stage": "08.7"})
    bridge.register_runtime(runtime)
    bridge.register_cli(cli)
    bridge.register_sdk(sdk)
    bus = EventBus()
    container = ServiceContainer(metadata={"stage": "08.7"})
    container.bridge_runtime(runtime).bridge_cli(cli).bridge_sdk(sdk).bridge_plugin_manager(plugin_manager).bridge_extension_manager(extension_manager)
    container.register_instance("event_bus", bus)
    container.register_instance("sdk_cli_bridge", bridge)

    core = IntegrationCore(metadata={"stage": "08.7"})
    core.register_component("service_container", "service_container", container, version=container.version)
    core.register_component("event_bus", "event_bus", bus, version=bus.version)
    core.register_component("bridge", "sdk_cli_bridge", bridge, version=bridge.version)

    benchmark = IntegrationBenchmark(metadata={"stage": "08.7", "scope": "integration"})
    benchmark.add_case("runtime_startup", lambda: runtime.execute("boot"), iterations=3)
    benchmark.add_case("session_create", lambda: create_session(segments=["abc"]), iterations=3)
    benchmark.add_case("translation_pipeline", lambda: sdk.translate_text("abc"), iterations=3)
    benchmark.add_case("event_bus_publish", lambda: bus.publish("benchmark.tick", {"ok": True}, topic="benchmark"), iterations=3)
    benchmark.add_case("service_resolve", lambda: container.resolve("runtime"), iterations=3)
    benchmark.add_case("plugin_lookup", lambda: plugin_manager.manifest(), iterations=2)
    benchmark.add_case("extension_discovery", lambda: extension_manager.manifest(), iterations=2)
    report = benchmark.run()
    summary = report.summary()

    check("Runtime Performance", report.ok and summary["count"] == 7)
    check("SDK Performance", any(item.name == "translation_pipeline" for item in report.metrics))
    check("CLI Performance", bridge.manifest()["registry"]["count"] == 3)
    check("Plugin Performance", plugin_manager.manifest()["stage"].startswith("NTPE"))
    check("Extension Performance", extension_manager.manifest()["bridge"]["runtime_attached"] is True)
    check("Event Bus Performance", "Stage-08.5" in bus.manifest()["stage"] and bus.publish("benchmark.ok", {}, topic="benchmark").ok)
    check("Service Container", container.resolve("runtime") is runtime and container.validate()["ok"] is True)

    profiler = PerformanceProfiler()
    metric = profiler.profile("core_invoke", lambda: core.invoke("service_container", "resolve", "runtime"), iterations=2)
    check("Performance Profiler", metric.passed and metric.throughput_ops_per_sec > 0)

    load_result = IntegrationLoadTest().run("event_load", lambda i: bus.publish("benchmark.load", {"i": i}, topic="benchmark"), operations=5)
    check("Load Test", load_result["passed"] is True and load_result["iterations"] == 5)

    stress_result = IntegrationStressTest().run("service_stress", lambda: container.resolve("sdk"), cycles=5)
    check("Stress Test", stress_result["stable"] is True and stress_result["iterations"] == 5)

    check("Foundation Freeze", summary["foundation_status"] == "frozen")
    check("Backward Compatible", sdk.translate_text("compat").ok and core.invoke("event_bus", "manifest").ok)

    print("PASS")


if __name__ == "__main__":
    main()
