from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.lcr_governance_freeze import count_production_hooks, validate_governance_freeze
from core.provider_failure_characterization.failure_types import FAILURE_TYPES

from .loader import (
    AUTHORIZATION_FIELDS,
    CLAIM_LEDGER_PATH,
    EXPECTED_SOURCE_MANIFEST_SHA256,
    TAXONOMY_PATH,
    canonical_payload_hash,
    resolve_allowed_file,
    sha256_bytes,
)
from .models import GovernanceBaselineReference


EXPECTED_CAPABILITY_COUNT = 18
EXPECTED_TAXONOMY_COUNT = 19
EXPECTED_PRODUCTION_HOOK_COUNT = 1


def validate_capability_registry(capabilities: object) -> tuple[str, ...]:
    if not isinstance(capabilities, list):
        return ("capability_registry_invalid",)
    violations: list[str] = []
    ids = [item.get("capability_id") for item in capabilities if isinstance(item, dict)]
    if len(capabilities) != EXPECTED_CAPABILITY_COUNT or len(ids) != EXPECTED_CAPABILITY_COUNT:
        violations.append("capability_count_changed")
    if len(ids) != len(set(ids)):
        violations.append("duplicate_capability_id")
    for item in capabilities:
        if not isinstance(item, dict) or not isinstance(item.get("capability_id"), str):
            violations.append("capability_record_invalid")
            continue
        capability_id = item["capability_id"]
        if item.get("frozen") is not True or item.get("status") != "governance_frozen":
            violations.append(f"capability_not_frozen:{capability_id}")
        if any(item.get(field) is not False for field in (
            "active_integration", "production_write_allowed", "provider_execution_allowed"
        )):
            violations.append(f"capability_boundary_relaxed:{capability_id}")
    return tuple(sorted(set(violations)))


def validate_dependency_graph(graph: object, capability_ids: set[str]) -> tuple[str, ...]:
    if not isinstance(graph, dict):
        return ("dependency_graph_invalid",)
    violations: list[str] = []
    if set(graph) != capability_ids:
        violations.append("dependency_graph_capability_set_mismatch")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            violations.append("dependency_cycle")
            return
        if node in visited:
            return
        visiting.add(node)
        dependencies = graph.get(node, [])
        if not isinstance(dependencies, list):
            violations.append(f"dependency_list_invalid:{node}")
            dependencies = []
        for dependency in dependencies:
            if dependency == node:
                violations.append(f"self_dependency:{node}")
            elif dependency not in capability_ids:
                violations.append(f"orphan_dependency:{node}:{dependency}")
            else:
                visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for capability_id in sorted(capability_ids):
        visit(capability_id)
    return tuple(sorted(set(violations)))


def validate_taxonomy_payload(payload: object) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ("taxonomy_invalid",)
    violations: list[str] = []
    if payload.get("failure_type_count") != EXPECTED_TAXONOMY_COUNT:
        violations.append("taxonomy_count_changed")
    if payload.get("failure_types_added") != 0:
        violations.append("taxonomy_addition_detected")
    if payload.get("classification_semantics_modified") is not False:
        violations.append("taxonomy_semantics_changed")
    if payload.get("deterministic") is not True:
        violations.append("taxonomy_not_deterministic")
    if len(FAILURE_TYPES) != EXPECTED_TAXONOMY_COUNT:
        violations.append("runtime_taxonomy_count_changed")
    return tuple(sorted(violations))


def validate_claim_payload(payload: object) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ("claim_ledger_invalid",)
    violations: list[str] = []
    if payload.get("authorization_consumed") is not True:
        violations.append("claim_not_consumed")
    if payload.get("additional_execution_allowed") is not False:
        violations.append("claim_replay_allowed")
    if payload.get("response_status_classification") != "timeout":
        violations.append("claim_outcome_changed")
    if any(payload.get(name) is not False for name in (
        "formal_output_changed", "resume_changed", "cache_changed",
        "character_store_changed", "context_store_changed",
    )):
        violations.append("claim_production_state_changed")
    return tuple(sorted(violations))


def validate_authorization_state(state: object) -> tuple[str, ...]:
    if not isinstance(state, Mapping) or set(state) != set(AUTHORIZATION_FIELDS):
        return ("authorization_schema_invalid",)
    return tuple(
        f"authorization_relaxed:{field}"
        for field in AUTHORIZATION_FIELDS
        if state.get(field) is not False
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _hash_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def verify_governance_baseline(
    reference: GovernanceBaselineReference,
    payload: Mapping[str, Any],
    root: str | Path,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    base = Path(root).resolve(strict=True)
    violations: list[str] = []
    evidence: list[str] = []

    source = resolve_allowed_file(base, reference.source_manifest_path)
    if _hash_file(source) != reference.source_manifest_sha256 or reference.source_manifest_sha256 != EXPECTED_SOURCE_MANIFEST_SHA256:
        violations.append("source_manifest_hash_mismatch")
    else:
        evidence.append(f"source_manifest_sha256={reference.source_manifest_sha256}")

    for relative, expected in reference.child_manifest_hashes.items():
        try:
            child = resolve_allowed_file(base, relative)
        except Exception as exc:
            violations.append(str(exc))
            continue
        if _hash_file(child) != expected:
            violations.append(f"child_manifest_hash_mismatch:{relative}")
    if not any(item.startswith(("child_manifest", "required_file", "path_", "symlink_")) for item in violations):
        evidence.append(f"child_manifest_count={len(reference.child_manifest_hashes)}")

    capabilities = payload.get("capabilities")
    capability_violations = list(validate_capability_registry(capabilities))
    if canonical_payload_hash(capabilities) != reference.capability_registry_hash:
        capability_violations.append("capability_registry_hash_mismatch")
    violations.extend(capability_violations)
    capability_ids = {
        item["capability_id"] for item in capabilities
        if isinstance(item, dict) and isinstance(item.get("capability_id"), str)
    } if isinstance(capabilities, list) else set()
    if not capability_violations:
        evidence.append(f"capability_count={len(capability_ids)}")

    graph = payload.get("dependency_graph")
    dependency_violations = list(validate_dependency_graph(graph, capability_ids))
    if canonical_payload_hash(graph) != reference.dependency_graph_hash:
        dependency_violations.append("dependency_graph_hash_mismatch")
    violations.extend(dependency_violations)
    if not dependency_violations:
        dependency_count = sum(len(items) for items in graph.values())
        evidence.append(f"dependency_count={dependency_count}")

    taxonomy_path = resolve_allowed_file(base, TAXONOMY_PATH)
    taxonomy_violations = list(validate_taxonomy_payload(_read_json(taxonomy_path)))
    if _hash_file(taxonomy_path) != reference.taxonomy_hash:
        taxonomy_violations.append("taxonomy_hash_mismatch")
    violations.extend(taxonomy_violations)
    if not taxonomy_violations:
        evidence.append(f"taxonomy_count={EXPECTED_TAXONOMY_COUNT}")

    claim_path = resolve_allowed_file(base, CLAIM_LEDGER_PATH)
    claim_violations = list(validate_claim_payload(_read_json(claim_path)))
    if _hash_file(claim_path) != reference.claim_ledger_hash:
        claim_violations.append("claim_ledger_hash_mismatch")
    violations.extend(claim_violations)
    if not claim_violations:
        evidence.append("consumed_claims=1")

    actual_hooks = count_production_hooks(base)
    if reference.production_hook_count != EXPECTED_PRODUCTION_HOOK_COUNT or actual_hooks != EXPECTED_PRODUCTION_HOOK_COUNT:
        violations.append("production_hook_count_changed")
    else:
        evidence.append("production_hook_count=1")

    authorization_violations = validate_authorization_state(reference.authorization_state)
    violations.extend(authorization_violations)
    if not authorization_violations:
        evidence.append("authorization_state=all_false")

    freeze_errors = validate_governance_freeze(base)
    violations.extend(f"batch110_freeze:{item}" for item in freeze_errors)
    if not freeze_errors:
        evidence.append("batch110_freeze_regression=PASS")

    return tuple(sorted(set(violations))), tuple(sorted(evidence))
