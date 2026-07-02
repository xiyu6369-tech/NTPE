"""NTPE 1.0 Beta Stage-10.1 Platform Service Configuration test."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_services import (  # noqa: E402
    PLATFORM_CONFIG_STAGE,
    PlatformConfigStore,
    create_platform_config,
    create_platform_service_host,
    create_service_config,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<34} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


class ConfiguredService:
    def __init__(self, config):
        self.config = config
        self.started_with = None

    def start(self):
        self.started_with = self.config.as_kwargs(["enabled", "max_workers"])
        return self.started_with

    def stop(self):
        return {"stopped": True}


def main() -> None:
    print("NTPE 1.0 Beta Stage-10.1 Platform Service Configuration Test")
    print("=" * 78)

    base = create_platform_config({"enabled": True, "max_workers": 2}, source="base")
    override = PlatformConfigStore({"max_workers": 4, "retry_limit": 3}, source="override")
    merged = base.merge(override)

    check("Config Stage", PLATFORM_CONFIG_STAGE == "10.1")
    check("Config Merge", merged.require("max_workers") == 4 and merged.require("enabled") is True)
    check("Config Manifest", merged.manifest()["count"] == 3 and merged.manifest()["stage"] == "10.1")

    service_config = create_service_config(
        "configured_worker",
        defaults={"enabled": False, "timeout": 30},
        overrides={"enabled": True},
        store=merged,
        metadata={"stage": "10.1"},
    )
    check("Service Config", service_config.require("enabled") is True and service_config.require("timeout") == 30)
    check("Service Kwargs", service_config.as_kwargs(["max_workers", "retry_limit"]) == {"max_workers": 4, "retry_limit": 3})

    host = create_platform_service_host(metadata={"stage": "10.1"})
    service = ConfiguredService(service_config)
    descriptor = host.register_service("configured_worker", service, metadata={"config_stage": service_config.stage})
    check("Host Registration", descriptor.name == "configured_worker")
    results = host.start()
    check("Configured Start", all(result.ok for result in results) and service.started_with["max_workers"] == 4)
    health = host.health()
    check("Health Compatible", health["ok"] is True and health["count"] == 1)

    manifest = service_config.manifest()
    check("Foundation Compatible", manifest["foundation_status"] == "frozen")
    check("CLI Compatible", manifest["cli_status"] == "frozen")
    check("SDK Compatible", manifest["sdk_status"] == "complete")
    check("Integration Compatible", manifest["integration_status"] == "frozen")
    check("Workflow Compatible", manifest["workflow_status"] == "frozen")
    check("Additive Only", manifest["additive_only"] is True)

    print("PASS")


if __name__ == "__main__":
    main()
