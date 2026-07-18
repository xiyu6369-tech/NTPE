from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class GovernanceBaselineReference:
    schema_version: str
    batch_id: str
    activation_gate: str
    source_manifest_path: str
    source_manifest_sha256: str
    child_manifest_hashes: Mapping[str, str]
    capability_registry_hash: str
    dependency_graph_hash: str
    taxonomy_hash: str
    claim_ledger_hash: str
    production_hook_count: int
    authorization_state: Mapping[str, bool]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "batch_id": self.batch_id,
            "activation_gate": self.activation_gate,
            "source_manifest_path": self.source_manifest_path,
            "source_manifest_sha256": self.source_manifest_sha256,
            "child_manifest_hashes": dict(self.child_manifest_hashes),
            "capability_registry_hash": self.capability_registry_hash,
            "dependency_graph_hash": self.dependency_graph_hash,
            "taxonomy_hash": self.taxonomy_hash,
            "claim_ledger_hash": self.claim_ledger_hash,
            "production_hook_count": self.production_hook_count,
            "authorization_state": dict(self.authorization_state),
        }


@dataclass(frozen=True)
class GovernanceConsumptionAuditResult:
    status: str
    baseline_verified: bool
    manifest_hashes_verified: bool
    capability_registry_verified: bool
    dependency_graph_verified: bool
    taxonomy_verified: bool
    claim_ledger_verified: bool
    production_hook_count_verified: bool
    authorization_state_verified: bool
    violations: tuple[str, ...]
    evidence: tuple[str, ...]
    deterministic_fingerprint: str

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "baseline_verified": self.baseline_verified,
            "manifest_hashes_verified": self.manifest_hashes_verified,
            "capability_registry_verified": self.capability_registry_verified,
            "dependency_graph_verified": self.dependency_graph_verified,
            "taxonomy_verified": self.taxonomy_verified,
            "claim_ledger_verified": self.claim_ledger_verified,
            "production_hook_count_verified": self.production_hook_count_verified,
            "authorization_state_verified": self.authorization_state_verified,
            "violations": list(self.violations),
            "evidence": list(self.evidence),
            "deterministic_fingerprint": self.deterministic_fingerprint,
        }
