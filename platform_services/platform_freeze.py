"""Platform Services freeze manifest for NTPE 1.0 Beta Stage-10.8.

Stage-10.8 freezes the Platform Services public contract created across
Stage-10.0 through Stage-10.7. The module is additive and does not mutate
Foundation, CLI, SDK, Integration, Workflow, or existing Platform Services
runtime behavior.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

PLATFORM_FREEZE_VERSION = "1.0.0-beta.10.8"
PLATFORM_FREEZE_STAGE = "10.8"
PLATFORM_FREEZE_STATUS = "frozen"

PLATFORM_FROZEN_SURFACES = (
    "platform_models",
    "service_registry",
    "service_manager",
    "service_host",
    "platform_config",
    "service_discovery",
    "health_status",
    "health_monitor",
    "metrics_snapshot",
    "telemetry",
    "metrics",
    "event_bus",
    "event_bridge",
    "lifecycle_hooks",
    "service_lifecycle",
    "service_policy",
    "policy_registry",
    "policy_engine",
)

PLATFORM_STAGE_MATRIX = {
    "stage_10_0_platform_services": True,
    "stage_10_1_platform_config": True,
    "stage_10_2_service_discovery": True,
    "stage_10_3_service_health_monitor": True,
    "stage_10_4_metrics_telemetry": True,
    "stage_10_5_event_bus": True,
    "stage_10_6_lifecycle_hooks": True,
    "stage_10_7_policy_layer": True,
}


@dataclass(frozen=True)
class PlatformFreezeValidation:
    ok: bool
    status: str
    errors: list[str] = field(default_factory=list)
    manifest: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "errors": list(self.errors),
            "manifest": dict(self.manifest),
        }


def build_platform_freeze_manifest(metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": "NTPE Platform Services",
        "version": PLATFORM_FREEZE_VERSION,
        "stage": PLATFORM_FREEZE_STAGE,
        "status": PLATFORM_FREEZE_STATUS,
        "foundation_status": "frozen",
        "cli_status": "frozen",
        "sdk_status": "complete",
        "integration_status": "frozen",
        "workflow_status": "frozen",
        "platform_services_status": "frozen",
        "additive_only": True,
        "backward_compatible": True,
        "frozen_surfaces": list(PLATFORM_FROZEN_SURFACES),
        "stage_matrix": dict(PLATFORM_STAGE_MATRIX),
        "metadata": dict(metadata or {}),
    }


def build_platform_service_contract() -> Dict[str, Any]:
    return {
        "version": PLATFORM_FREEZE_VERSION,
        "status": PLATFORM_FREEZE_STATUS,
        "frozen_surfaces": list(PLATFORM_FROZEN_SURFACES),
        "rules": {
            "backward_compatible": True,
            "additive_only": True,
            "no_frozen_module_mutation": True,
            "public_api_stable": True,
            "future_changes_require_new_stage": True,
        },
    }


def build_platform_compatibility_matrix() -> Dict[str, Any]:
    return {
        "version": PLATFORM_FREEZE_VERSION,
        "status": PLATFORM_FREEZE_STATUS,
        "matrix": {
            "foundation_v1_freeze": True,
            "cli_freeze": True,
            "sdk_stage_07": True,
            "integration_freeze": True,
            "workflow_freeze": True,
            **dict(PLATFORM_STAGE_MATRIX),
        },
    }


def build_platform_version_manifest() -> Dict[str, Any]:
    return {
        "component": "platform_services",
        "version": PLATFORM_FREEZE_VERSION,
        "stage": PLATFORM_FREEZE_STAGE,
        "status": PLATFORM_FREEZE_STATUS,
        "api_contract": "frozen",
    }


def platform_freeze_is_compatible(matrix: Mapping[str, Any]) -> bool:
    values = matrix.get("matrix", {}) if isinstance(matrix, Mapping) else {}
    return bool(values) and all(value is True for value in values.values())


def validate_platform_freeze_manifest(manifest: Mapping[str, Any]) -> PlatformFreezeValidation:
    errors: list[str] = []
    if manifest.get("version") != PLATFORM_FREEZE_VERSION:
        errors.append("invalid freeze version")
    if manifest.get("stage") != PLATFORM_FREEZE_STAGE:
        errors.append("invalid freeze stage")
    if manifest.get("status") != PLATFORM_FREEZE_STATUS:
        errors.append("platform services status is not frozen")
    for key in ("foundation_status", "cli_status", "integration_status", "workflow_status"):
        if manifest.get(key) != "frozen":
            errors.append(f"{key} is not frozen")
    if manifest.get("sdk_status") != "complete":
        errors.append("sdk_status is not complete")
    if manifest.get("additive_only") is not True:
        errors.append("additive_only must be true")
    if manifest.get("backward_compatible") is not True:
        errors.append("backward_compatible must be true")
    surfaces = manifest.get("frozen_surfaces", [])
    missing = [surface for surface in PLATFORM_FROZEN_SURFACES if surface not in surfaces]
    if missing:
        errors.append("missing frozen surfaces: " + ", ".join(missing))
    matrix = manifest.get("stage_matrix", {})
    if not matrix or not all(matrix.get(key) is True for key in PLATFORM_STAGE_MATRIX):
        errors.append("stage matrix is incomplete")
    return PlatformFreezeValidation(ok=not errors, status=manifest.get("status", "unknown"), errors=errors, manifest=dict(manifest))


def write_platform_freeze_artifacts(directory: str | Path, metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, str]:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "platform_freeze_manifest.json": build_platform_freeze_manifest(metadata),
        "platform_service_contract.json": build_platform_service_contract(),
        "platform_compatibility_matrix.json": build_platform_compatibility_matrix(),
        "platform_version_manifest.json": build_platform_version_manifest(),
    }
    written: Dict[str, str] = {}
    for name, payload in artifacts.items():
        target = path / name
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        written[name] = str(target)
    return written


def load_platform_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
