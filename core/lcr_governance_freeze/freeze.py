from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .contracts import GOVERNANCE_CONTRACTS
from .registry import CAPABILITY_REGISTRY
from .validation import sha256_file, validate_contracts, validate_hashes, validate_registry


COMPONENT_NAME = "legacy_capability_recovery_governance"
FREEZE_VERSION = "LCR-Batch-11.0"
GOVERNANCE_SCHEMA_VERSION = "1.0"
FROZEN_AT = "2026-07-18T16:27:00Z"
ACTIVATION_GATE = "lcr_governance_baseline_frozen"
COVERED_BATCHES = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "10.1", "10.2", "10.3", "10.4", "10.5", "10.6", "10.7", "10.8", "10.9")
SOURCE_FILES = (
    "core/lcr_governance_freeze/__init__.py",
    "core/lcr_governance_freeze/registry.py",
    "core/lcr_governance_freeze/contracts.py",
    "core/lcr_governance_freeze/validation.py",
)


@dataclass(frozen=True)
class GovernanceFreezeMetadata:
    component_name: str
    freeze_version: str
    governance_schema_version: str
    covered_batches: tuple[str, ...]
    capability_count: int
    frozen_capability_count: int
    production_hook_count: int
    provider_execution_history: tuple[str, ...]
    active_production_authorized: bool
    automatic_rollout_authorized: bool
    production_integration_authorized: bool
    formal_output_replacement_authorized: bool
    source_files: tuple[str, ...]
    source_hashes: Mapping[str, str]
    manifest_hashes: Mapping[str, str]
    frozen_at: str
    activation_gate: str

    def to_dict(self) -> dict[str, object]:
        return {
            "component_name": self.component_name,
            "freeze_version": self.freeze_version,
            "governance_schema_version": self.governance_schema_version,
            "covered_batches": list(self.covered_batches),
            "capability_count": self.capability_count,
            "frozen_capability_count": self.frozen_capability_count,
            "production_hook_count": self.production_hook_count,
            "provider_execution_history": list(self.provider_execution_history),
            "active_production_authorized": self.active_production_authorized,
            "automatic_rollout_authorized": self.automatic_rollout_authorized,
            "production_integration_authorized": self.production_integration_authorized,
            "formal_output_replacement_authorized": self.formal_output_replacement_authorized,
            "source_files": list(self.source_files),
            "source_hashes": dict(self.source_hashes),
            "manifest_hashes": dict(self.manifest_hashes),
            "frozen_at": self.frozen_at,
            "activation_gate": self.activation_gate,
        }


def get_governance_freeze_metadata(root: str | Path | None = None) -> GovernanceFreezeMetadata:
    base = Path(root).resolve() if root is not None else Path(__file__).resolve().parents[2]
    source_hashes = MappingProxyType({relative: sha256_file(base / relative) for relative in SOURCE_FILES})
    child_paths = tuple(dict.fromkeys(item.manifest_path for item in CAPABILITY_REGISTRY))
    manifest_hashes = MappingProxyType({relative: sha256_file(base / relative) for relative in child_paths})
    return GovernanceFreezeMetadata(
        component_name=COMPONENT_NAME,
        freeze_version=FREEZE_VERSION,
        governance_schema_version=GOVERNANCE_SCHEMA_VERSION,
        covered_batches=COVERED_BATCHES,
        capability_count=len(CAPABILITY_REGISTRY),
        frozen_capability_count=sum(item.frozen for item in CAPABILITY_REGISTRY),
        production_hook_count=GOVERNANCE_CONTRACTS.production_hook_count,
        provider_execution_history=("Batch 10.7: one authorized request consumed; timeout; no candidate; no production change",),
        active_production_authorized=False,
        automatic_rollout_authorized=False,
        production_integration_authorized=False,
        formal_output_replacement_authorized=False,
        source_files=SOURCE_FILES,
        source_hashes=source_hashes,
        manifest_hashes=manifest_hashes,
        frozen_at=FROZEN_AT,
        activation_gate=ACTIVATION_GATE,
    )


def validate_governance_freeze(root: str | Path | None = None) -> tuple[str, ...]:
    base = Path(root).resolve() if root is not None else Path(__file__).resolve().parents[2]
    metadata = get_governance_freeze_metadata(base)
    errors = list(validate_registry(CAPABILITY_REGISTRY, base))
    errors.extend(validate_contracts(GOVERNANCE_CONTRACTS, base))
    errors.extend(validate_hashes(base, metadata.source_hashes))
    errors.extend(validate_hashes(base, metadata.manifest_hashes))
    if metadata.capability_count != 18 or metadata.frozen_capability_count != 18:
        errors.append("capability_count_changed")
    if metadata.covered_batches != COVERED_BATCHES:
        errors.append("covered_batches_changed")
    return tuple(errors)
