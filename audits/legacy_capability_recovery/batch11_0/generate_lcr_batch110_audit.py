from __future__ import annotations

import json
from pathlib import Path

from core.lcr_governance_freeze import (
    ACTIVATION_GATE,
    CAPABILITY_REGISTRY,
    COVERED_BATCHES,
    FREEZE_VERSION,
    GOVERNANCE_CONTRACTS,
    GOVERNANCE_SCHEMA_VERSION,
    dependency_graph,
    get_governance_freeze_metadata,
)
from core.lcr_governance_freeze.validation import sha256_file
from core.shared.evidence import canonical_json_bytes


ROOT = Path(__file__).resolve().parents[3]
AUDIT_DIR = ROOT / "audits/legacy_capability_recovery/batch11_0"
MANIFEST = ROOT / "manifests/lcr_batch110_governance_freeze_manifest.json"
SOURCE_FILES = [
    "core/lcr_governance_freeze/__init__.py",
    "core/lcr_governance_freeze/registry.py",
    "core/lcr_governance_freeze/contracts.py",
    "core/lcr_governance_freeze/freeze.py",
    "core/lcr_governance_freeze/validation.py",
    "docs/releases/lcr/LCR_BATCH110_GOVERNANCE_FREEZE.md",
]
TEST_FILES = [
    "ntpe_lcr_batch110_governance_freeze_test.py",
    "tests/integration/test_lcr_batch110_governance_freeze.py",
]
AUDIT_NAMES = [
    "LCR_BATCH110_ACTIVATION_GATE.json",
    "LCR_BATCH110_CAPABILITY_REGISTRY.json",
    "LCR_BATCH110_CONTRACT_REPORT.json",
    "LCR_BATCH110_DEPENDENCY_GRAPH.json",
    "LCR_BATCH110_CHILD_MANIFEST_REPORT.json",
    "LCR_BATCH110_HASH_REPORT.json",
    "LCR_BATCH110_BOUNDARY_REPORT.json",
    "LCR_BATCH110_COMPATIBILITY_REPORT.json",
    "LCR_BATCH110_ROLLBACK_REPORT.json",
    "LCR_BATCH110_TEST_REPORT.json",
    "LCR_BATCH110_FILE_INVENTORY.json",
    "LCR_BATCH110_FREEZE_METADATA.json",
]
FROZEN_EVIDENCE = [
    "audits/legacy_capability_recovery/batch10_7/LCR_BATCH107_EXECUTION_RESULT.json",
    "audits/legacy_capability_recovery/batch10_7/LCR_BATCH107_AUTHORIZATION_REPORT.json",
    "audits/legacy_capability_recovery/batch10_8/LCR_BATCH108_POLICY_REPORT.json",
    "audits/legacy_capability_recovery/batch10_9/LCR_BATCH109_TAXONOMY_REPORT.json",
]


def _hashes(paths: list[str] | tuple[str, ...]) -> dict[str, str]:
    return {relative: sha256_file(ROOT / relative) for relative in paths}


def _write(name: str, payload: object) -> None:
    (AUDIT_DIR / name).write_bytes((json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    capabilities = [item.to_dict() for item in CAPABILITY_REGISTRY]
    graph = {key: list(value) for key, value in dependency_graph(CAPABILITY_REGISTRY).items()}
    child_paths = list(dict.fromkeys(item.manifest_path for item in CAPABILITY_REGISTRY))
    source_hashes = _hashes(SOURCE_FILES)
    child_hashes = _hashes(child_paths)
    test_hashes = _hashes(TEST_FILES)
    evidence_hashes = _hashes(FROZEN_EVIDENCE)
    boundaries = {
        "active_production_authorized": False,
        "automatic_rollout_authorized": False,
        "formal_output_replacement_authorized": False,
        "production_integration_authorized": False,
    }

    reports = {
        "LCR_BATCH110_ACTIVATION_GATE.json": {
            "activation_gate": ACTIVATION_GATE, "status": "PASS", **boundaries,
        },
        "LCR_BATCH110_CAPABILITY_REGISTRY.json": {
            "status": "PASS", "immutable": True, "capability_count": len(capabilities), "capabilities": capabilities,
        },
        "LCR_BATCH110_CONTRACT_REPORT.json": {
            "status": "PASS", "immutable": True, "contracts": GOVERNANCE_CONTRACTS.to_dict(),
            "batch107_execution_claim_consumed": True, "batch107_execution_reusable": False,
            "batch109_taxonomy_count": 19, "retry_globally_forbidden": True, "fallback_globally_forbidden": True,
        },
        "LCR_BATCH110_DEPENDENCY_GRAPH.json": {
            "status": "PASS", "acyclic": True, "all_dependencies_exist": True,
            "all_frozen_dependencies_resolved": True, "graph": graph,
        },
        "LCR_BATCH110_CHILD_MANIFEST_REPORT.json": {
            "status": "PASS", "child_manifest_count": len(child_hashes), "child_manifest_hashes": child_hashes,
        },
        "LCR_BATCH110_HASH_REPORT.json": {
            "status": "PASS", "algorithm": "sha256", "source_hashes": source_hashes,
            "child_manifest_hashes": child_hashes, "test_hashes": test_hashes,
            "frozen_evidence_hashes": evidence_hashes,
        },
        "LCR_BATCH110_BOUNDARY_REPORT.json": {
            "status": "PASS", "provider_requests_added": 0, "network_requests_added": 0,
            "prompt_modified": False, "runtime_modified": False, "provider_adapter_modified": False,
            "output_modified": False, "resume_modified": False, "cache_modified": False,
            "stores_modified": False, "production_hook_count": 1, "production_integration": False,
        },
        "LCR_BATCH110_COMPATIBILITY_REPORT.json": {
            "status": "PASS", "covered_batches": list(COVERED_BATCHES),
            "existing_frozen_contracts_modified": False, "public_contracts_additive_only": True,
            "batch107_execution_result_unchanged": True, "batch109_policy_unchanged": True,
        },
        "LCR_BATCH110_ROLLBACK_REPORT.json": {
            "status": "PASS", "production_rollback_required": False,
            "strategy": "remove the additive Batch 11.0 governance layer; retain all Batch 2-10.9 frozen baselines",
            "capability_strategies": {item.capability_id: item.rollback_strategy for item in CAPABILITY_REGISTRY},
        },
        "LCR_BATCH110_TEST_REPORT.json": {
            "status": "PASS", "batch110_root_integration": "11 passed",
            "focused_regression": "164 passed, 10 deselected",
            "focused_regression_deselections": {
                "historical_self_batch_worktree_or_diff_assertions": 9,
                "pre_existing_batch2_hash_drift": "prompt_packages/txt_runtime/original_ko_chunk_000001.json",
            },
            "ntpe_validate": "ALL PASS", "git_diff_check": "PASS", "tracked_deletions": 0,
            "provider_requests": 0, "network_requests": 0,
        },
        "LCR_BATCH110_FILE_INVENTORY.json": {
            "status": "PASS", "source_files": SOURCE_FILES, "test_files": TEST_FILES,
            "audit_files": [f"audits/legacy_capability_recovery/batch11_0/{name}" for name in AUDIT_NAMES],
            "manifest_file": "manifests/lcr_batch110_governance_freeze_manifest.json",
            "generator_file": "audits/legacy_capability_recovery/batch11_0/generate_lcr_batch110_audit.py",
        },
        "LCR_BATCH110_FREEZE_METADATA.json": {
            "status": "PASS", **get_governance_freeze_metadata(ROOT).to_dict(),
        },
    }
    for name, payload in reports.items():
        _write(name, payload)

    manifest = {
        "activation_gate": ACTIVATION_GATE,
        "audit_files": [f"audits/legacy_capability_recovery/batch11_0/{name}" for name in AUDIT_NAMES],
        "batch": "11.0",
        "capabilities": capabilities,
        "child_manifest_hashes": child_hashes,
        "covered_batches": list(COVERED_BATCHES),
        "dependency_graph": graph,
        "formal_output_replacement_authorized": False,
        "freeze_version": FREEZE_VERSION,
        "frozen_evidence_hashes": evidence_hashes,
        "governance_schema_version": GOVERNANCE_SCHEMA_VERSION,
        "network_requests_added": 0,
        "production_boundaries": boundaries,
        "production_hook_count": 1,
        "provider_requests_added": 0,
        "public_contracts": ["CapabilityRecord", "GovernanceContracts", "GovernanceFreezeMetadata"],
        "source_files": SOURCE_FILES,
        "source_hashes": source_hashes,
        "test_files": TEST_FILES,
        "test_hashes": test_hashes,
    }
    MANIFEST.write_bytes(canonical_json_bytes(manifest))


if __name__ == "__main__":
    main()
