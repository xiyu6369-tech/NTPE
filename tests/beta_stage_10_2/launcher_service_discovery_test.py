"""NTPE 1.0 Beta Stage-10.2 Service Discovery test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_services import (  # noqa: E402
    PLATFORM_DISCOVERY_STAGE,
    PlatformServiceDiscovery,
    PlatformServiceStatus,
    ServiceDiscoveryQuery,
    create_platform_service_host,
    create_service_discovery,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class DemoService:
    def start(self):
        return {"started": True}

    def stop(self):
        return {"stopped": True}


def main() -> None:
    print("NTPE 1.0 Beta Stage-10.2 Service Discovery Test")
    print("=" * 78)

    host = create_platform_service_host(metadata={"stage": "10.2"})
    host.register_service("config_service", DemoService(), metadata={"tags": ["platform", "config"], "tier": "core"})
    host.register_service("worker_service", DemoService(), dependencies=["config_service"], metadata={"tags": ["platform", "worker"], "tier": "runtime"})
    host.register_service("optional_service", None, metadata={"tags": "optional", "tier": "extension"})

    discovery = create_service_discovery(host.manager.registry, metadata={"stage": "10.2"})

    check("Discovery Stage", PLATFORM_DISCOVERY_STAGE == "10.2")
    check("Discovery Type", isinstance(discovery, PlatformServiceDiscovery))
    check("By Name", discovery.by_name("config_service").name == "config_service")
    check("Require Service", discovery.require("worker_service").metadata["tier"] == "runtime")
    check("By Tag", discovery.by_tag("platform").count == 2)
    check("Metadata Match", discovery.metadata_match(tier="extension").names() == ["optional_service"])
    check("Dependency Match", discovery.depending_on("config_service").names() == ["worker_service"])

    results = host.start()
    check("Host Start", all(result.ok for result in results))
    running = discovery.running().names()
    check("Running Discovery", "config_service" in running and "worker_service" in running)

    query = ServiceDiscoveryQuery(status=PlatformServiceStatus.RUNNING.value, metadata={"tier": "runtime"})
    query_result = discovery.discover(query)
    check("Query Object", query_result.names() == ["worker_service"])
    check("Result Manifest", query_result.manifest()["stage"] == "10.2" and query_result.manifest()["count"] == 1)

    manifest = discovery.manifest()
    check("Foundation Compatible", manifest["foundation_status"] == "frozen")
    check("CLI Compatible", manifest["cli_status"] == "frozen")
    check("SDK Compatible", manifest["sdk_status"] == "complete")
    check("Integration Compatible", manifest["integration_status"] == "frozen")
    check("Workflow Compatible", manifest["workflow_status"] == "frozen")
    check("Additive Only", manifest["additive_only"] is True)

    print("PASS")


if __name__ == "__main__":
    main()
