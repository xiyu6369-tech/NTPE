"""NTPE Stage-08.8 Integration Freeze helpers.

This module is additive. It freezes the Integration v1.0 public contract
without modifying Foundation, CLI, SDK, Runtime, Plugin, Extension, Event Bus,
or Service Container implementations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List
import json

INTEGRATION_FREEZE_VERSION = "1.0.0"
INTEGRATION_FREEZE_STAGE = "NTPE 1.0 Beta Stage-08.8 Integration Freeze"
INTEGRATION_FREEZE_STATUS = "frozen"
FOUNDATION_FREEZE_STATUS = "frozen"

REQUIRED_CONTRACTS = [
    "integration_core",
    "runtime_integration",
    "sdk_cli_bridge",
    "plugin_integration",
    "extension_framework",
    "event_bus",
    "service_container",
]

COMPATIBILITY_TARGETS = [
    "foundation_v1",
    "cli_freeze",
    "sdk_stage_07",
    "runtime_integration",
    "plugin_integration",
    "extension_framework",
    "event_bus",
    "service_container",
]


@dataclass
class IntegrationFreezeResult:
    ok: bool
    status: str
    version: str = INTEGRATION_FREEZE_VERSION
    contracts: List[str] = field(default_factory=list)
    compatibility: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "version": self.version,
            "contracts": list(self.contracts),
            "compatibility": dict(self.compatibility),
            "errors": list(self.errors),
        }


def build_freeze_manifest(metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "name": "ntpe-integration",
        "version": INTEGRATION_FREEZE_VERSION,
        "stage": INTEGRATION_FREEZE_STAGE,
        "status": INTEGRATION_FREEZE_STATUS,
        "foundation_status": FOUNDATION_FREEZE_STATUS,
        "additive_only": True,
        "contracts": list(REQUIRED_CONTRACTS),
        "compatibility_targets": list(COMPATIBILITY_TARGETS),
        "metadata": dict(metadata or {}),
    }


def build_integration_contract() -> Dict[str, Any]:
    return {
        "contract_version": INTEGRATION_FREEZE_VERSION,
        "status": INTEGRATION_FREEZE_STATUS,
        "frozen_surfaces": {
            "integration_core": ["IntegrationCore", "IntegrationRegistry", "IntegrationContext", "IntegrationResult"],
            "runtime_integration": ["RuntimeBridge", "RuntimeManager", "RuntimeRegistry", "RuntimeDispatcher"],
            "sdk_cli_bridge": ["SDKCLIBridge", "BridgeManager", "BridgeRegistry", "BridgeDispatcher"],
            "plugin_integration": ["PluginIntegrationBridge", "PluginIntegrationManager", "PluginIntegrationRegistry"],
            "extension_framework": ["ExtensionManager", "ExtensionRegistry", "ExtensionLoader", "ExtensionManifest"],
            "event_bus": ["EventBus", "EventPublisher", "EventSubscriber", "EventDispatcher"],
            "service_container": ["ServiceContainer", "ServiceRegistry", "ServiceProvider", "ServiceResolver"],
        },
        "rules": {
            "backward_compatible": True,
            "no_breaking_changes": True,
            "additive_extensions_allowed": True,
            "foundation_v1_required": True,
            "cli_freeze_required": True,
            "sdk_stage_07_required": True,
        },
    }


def build_compatibility_matrix() -> Dict[str, Any]:
    matrix = {target: True for target in COMPATIBILITY_TARGETS}
    return {
        "version": INTEGRATION_FREEZE_VERSION,
        "status": INTEGRATION_FREEZE_STATUS,
        "matrix": matrix,
        "compatible_with": [
            "Foundation v1.0 Frozen",
            "Stage-06 CLI Frozen",
            "Stage-07 SDK",
            "Stage-08.0 Integration Core",
            "Stage-08.1 Runtime Integration",
            "Stage-08.2 SDK-CLI Bridge",
            "Stage-08.3 Plugin Integration",
            "Stage-08.4 Extension Framework",
            "Stage-08.5 Event Bus",
            "Stage-08.6 Service Container",
            "Stage-08.7 Integration Benchmark",
        ],
    }


def build_version_manifest() -> Dict[str, Any]:
    return {
        "component": "integration",
        "version": INTEGRATION_FREEZE_VERSION,
        "stage": "08.8",
        "status": INTEGRATION_FREEZE_STATUS,
        "foundation_status": FOUNDATION_FREEZE_STATUS,
        "public_contract": "integration_contract.json",
        "compatibility_matrix": "compatibility_matrix.json",
    }


def validate_freeze_manifest(manifest: Dict[str, Any]) -> IntegrationFreezeResult:
    errors: List[str] = []
    contracts = list(manifest.get("contracts", []))
    compatibility_targets = list(manifest.get("compatibility_targets", []))
    compatibility = {target: target in compatibility_targets for target in COMPATIBILITY_TARGETS}

    if manifest.get("status") != INTEGRATION_FREEZE_STATUS:
        errors.append("integration status is not frozen")
    if manifest.get("foundation_status") != FOUNDATION_FREEZE_STATUS:
        errors.append("foundation status is not frozen")
    for contract in REQUIRED_CONTRACTS:
        if contract not in contracts:
            errors.append(f"missing contract: {contract}")
    for target in COMPATIBILITY_TARGETS:
        if target not in compatibility_targets:
            errors.append(f"missing compatibility target: {target}")

    return IntegrationFreezeResult(
        ok=not errors,
        status=str(manifest.get("status", "unknown")),
        contracts=contracts,
        compatibility=compatibility,
        errors=errors,
    )


def write_freeze_artifacts(directory: str | Path, metadata: Dict[str, Any] | None = None) -> Dict[str, Path]:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "freeze_manifest.json": build_freeze_manifest(metadata),
        "integration_contract.json": build_integration_contract(),
        "compatibility_matrix.json": build_compatibility_matrix(),
        "version_manifest.json": build_version_manifest(),
    }
    written: Dict[str, Path] = {}
    for name, payload in artifacts.items():
        target = path / name
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written[name] = target
    return written


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def freeze_is_compatible(matrix: Dict[str, Any], required: Iterable[str] | None = None) -> bool:
    values = dict(matrix.get("matrix", {}))
    keys = list(required or COMPATIBILITY_TARGETS)
    return all(values.get(key) is True for key in keys)
