from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

from core.provider_failure_characterization.execution_policy import EXECUTION_POLICIES
from core.provider_failure_characterization.failure_types import FAILURE_TYPES
from core.provider_failure_characterization.freeze import validate_provider_failure_policy_freeze

from .contracts import GovernanceContracts
from .registry import CapabilityRecord


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dependency_graph(registry: tuple[CapabilityRecord, ...]) -> dict[str, tuple[str, ...]]:
    return {item.capability_id: item.dependencies for item in registry}


def _has_cycle(graph: Mapping[str, tuple[str, ...]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(child) for child in graph.get(node, ())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def validate_registry(registry: tuple[CapabilityRecord, ...], root: str | Path) -> tuple[str, ...]:
    base = Path(root).resolve()
    errors: list[str] = []
    ids = tuple(item.capability_id for item in registry)
    known = set(ids)
    if len(ids) != len(set(ids)):
        errors.append("duplicate_capability_id")
    for item in registry:
        if not item.frozen:
            errors.append(f"capability_not_frozen:{item.capability_id}")
        if item.active_integration or item.production_write_allowed or item.provider_execution_allowed:
            errors.append(f"capability_boundary_relaxed:{item.capability_id}")
        for label, relative in (("manifest", item.manifest_path), ("audit", item.audit_path)):
            if not (base / relative).is_file():
                errors.append(f"{label}_missing:{item.capability_id}:{relative}")
        for dependency in item.dependencies:
            if dependency not in known:
                errors.append(f"dependency_missing:{item.capability_id}:{dependency}")
    if _has_cycle(dependency_graph(registry)):
        errors.append("dependency_cycle")
    return tuple(errors)


def count_production_hooks(root: str | Path) -> int:
    base = Path(root).resolve()
    # Keep the scanner's own source from becoming a false-positive hook site.
    needle = "run_read_only_lcr_shadow_" + "hook(package)"
    return sum(needle in path.read_text(encoding="utf-8") for path in (base / "core").rglob("*.py"))


def validate_contracts(contracts: GovernanceContracts, root: str | Path) -> tuple[str, ...]:
    base = Path(root).resolve()
    errors: list[str] = []
    if count_production_hooks(base) != contracts.production_hook_count:
        errors.append("production_hook_count_changed")
    forbidden_true = (
        "active_production_authorized", "production_integration_authorized",
        "automatic_rollout_authorized", "formal_output_replacement_authorized",
        "character_memory_production_write", "context_scene_production_write",
        "production_cache_changed", "resume_changed", "formal_output_changed",
        "dual_pass_candidate_replaces_production",
    )
    for name in forbidden_true:
        if getattr(contracts, name):
            errors.append(f"boundary_relaxed:{name}")
    required_true = (
        "batch107_execution_claim_consumed", "batch108_retry_globally_forbidden",
        "batch108_fallback_globally_forbidden", "batch109_policy_frozen",
        "semantic_verification_required", "semantic_failure_retains_production",
        "insufficient_evidence_requires_manual_review",
    )
    for name in required_true:
        if not getattr(contracts, name):
            errors.append(f"contract_disabled:{name}")
    if contracts.batch107_execution_reusable:
        errors.append("batch107_execution_reusable")

    result = json.loads((base / "audits/legacy_capability_recovery/batch10_7/LCR_BATCH107_EXECUTION_RESULT.json").read_text(encoding="utf-8"))
    if not result.get("authorization_consumed") or result.get("additional_execution_allowed"):
        errors.append("batch107_execution_claim_not_consumed")
    if any(result.get(name) for name in ("formal_output_changed", "resume_changed", "cache_changed", "character_store_changed", "context_store_changed")):
        errors.append("batch107_production_state_changed")
    if result.get("response_status_classification") != "timeout":
        errors.append("batch107_timeout_result_changed")
    if len(FAILURE_TYPES) != 19:
        errors.append("batch109_taxonomy_count_changed")
    if any(policy.retry_allowed for policy in EXECUTION_POLICIES.values()):
        errors.append("retry_policy_relaxed")
    if any(policy.fallback_allowed for policy in EXECUTION_POLICIES.values()):
        errors.append("fallback_policy_relaxed")
    errors.extend(f"batch109:{item}" for item in validate_provider_failure_policy_freeze(base))
    return tuple(errors)


def validate_hashes(root: str | Path, expected: Mapping[str, str]) -> tuple[str, ...]:
    base = Path(root).resolve()
    errors: list[str] = []
    for relative, digest in expected.items():
        path = base / relative
        if not path.is_file():
            errors.append(f"hash_source_missing:{relative}")
        elif sha256_file(path) != digest:
            errors.append(f"hash_mismatch:{relative}")
    return tuple(errors)
