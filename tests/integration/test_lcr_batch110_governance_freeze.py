from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path

import pytest

from core.lcr_governance_freeze import (
    ACTIVATION_GATE,
    CAPABILITIES_BY_ID,
    CAPABILITY_REGISTRY,
    GOVERNANCE_CONTRACTS,
    count_production_hooks,
    dependency_graph,
    get_governance_freeze_metadata,
    validate_contracts,
    validate_governance_freeze,
    validate_registry,
)
from core.provider_failure_characterization import FailureType, execution_policy
from core.shared.evidence import canonical_json_bytes


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "manifests/lcr_batch110_governance_freeze_manifest.json"
BATCH107_RESULT = ROOT / "audits/legacy_capability_recovery/batch10_7/LCR_BATCH107_EXECUTION_RESULT.json"
AUDIT_DIRECTORY = ROOT / "audits/legacy_capability_recovery/batch11_0"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_registry_contains_all_expected_capabilities_once():
    expected = (
        "character_memory_v2", "context_scene_memory", "chunk_cache_v2",
        "dual_pass_translation", "post_polish_semantic_verification",
        "multilingual_profiles", "controlled_provider_routing",
        "offline_golden_tic_validation", "production_shadow_planning",
        "read_only_production_shadow_hook", "character_memory_shadow",
        "context_scene_shadow", "dual_pass_semantic_shadow",
        "explicit_pilot_authorization", "single_chunk_execution_review",
        "real_provider_validation", "provider_failure_characterization",
        "provider_failure_policy_freeze",
    )
    assert tuple(item.capability_id for item in CAPABILITY_REGISTRY) == expected
    assert tuple(CAPABILITIES_BY_ID) == expected
    assert len(set(expected)) == 18


def test_registry_paths_dependencies_and_frozen_boundaries_validate():
    assert validate_registry(CAPABILITY_REGISTRY, ROOT) == ()
    assert all(item.frozen for item in CAPABILITY_REGISTRY)
    assert all(not item.active_integration for item in CAPABILITY_REGISTRY)
    assert all(not item.production_write_allowed for item in CAPABILITY_REGISTRY)
    assert all(not item.provider_execution_allowed for item in CAPABILITY_REGISTRY)


def test_dependency_graph_is_acyclic_and_resolved():
    graph = dependency_graph(CAPABILITY_REGISTRY)
    assert set(graph) == set(CAPABILITIES_BY_ID)
    assert all(dependency in graph for dependencies in graph.values() for dependency in dependencies)
    assert validate_registry(CAPABILITY_REGISTRY, ROOT) == ()


def test_registry_contracts_and_metadata_are_immutable():
    with pytest.raises(FrozenInstanceError):
        CAPABILITY_REGISTRY[0].frozen = False
    with pytest.raises(TypeError):
        CAPABILITY_REGISTRY[0] = CAPABILITY_REGISTRY[0]
    with pytest.raises(TypeError):
        CAPABILITIES_BY_ID["new"] = CAPABILITY_REGISTRY[0]
    with pytest.raises(FrozenInstanceError):
        GOVERNANCE_CONTRACTS.production_hook_count = 2
    metadata = get_governance_freeze_metadata(ROOT)
    with pytest.raises(FrozenInstanceError):
        metadata.active_production_authorized = True
    with pytest.raises(TypeError):
        metadata.source_hashes["new"] = "bad"


def test_cross_batch_contracts_and_single_hook_remain_frozen():
    assert validate_contracts(GOVERNANCE_CONTRACTS, ROOT) == ()
    assert count_production_hooks(ROOT) == GOVERNANCE_CONTRACTS.production_hook_count == 1
    assert GOVERNANCE_CONTRACTS.active_production_authorized is False
    assert GOVERNANCE_CONTRACTS.automatic_rollout_authorized is False
    assert GOVERNANCE_CONTRACTS.production_integration_authorized is False
    assert GOVERNANCE_CONTRACTS.formal_output_replacement_authorized is False


def test_batch107_execution_claim_is_consumed_and_result_is_unchanged():
    result = json.loads(BATCH107_RESULT.read_text(encoding="utf-8"))
    assert result["authorization_consumed"] is True
    assert result["additional_execution_allowed"] is False
    assert result["response_status_classification"] == "timeout"
    assert result["provider_requests"] == result["network_requests"] == 1
    assert result["formal_output_changed"] is False
    assert result["resume_changed"] is False
    assert result["cache_changed"] is False
    assert result["character_store_changed"] is False
    assert result["context_store_changed"] is False
    assert _manifest()["frozen_evidence_hashes"][BATCH107_RESULT.relative_to(ROOT).as_posix()] == _sha(BATCH107_RESULT)


def test_batch109_taxonomy_and_execution_policy_remain_frozen():
    assert len(FailureType) == 19
    assert all(not execution_policy(item).retry_allowed for item in FailureType)
    assert all(not execution_policy(item).fallback_allowed for item in FailureType)


def test_governance_metadata_is_complete_and_valid():
    metadata = get_governance_freeze_metadata(ROOT)
    assert metadata.capability_count == metadata.frozen_capability_count == 18
    assert metadata.production_hook_count == 1
    assert metadata.active_production_authorized is False
    assert metadata.automatic_rollout_authorized is False
    assert metadata.production_integration_authorized is False
    assert metadata.formal_output_replacement_authorized is False
    assert metadata.activation_gate == ACTIVATION_GATE == "lcr_governance_baseline_frozen"
    assert validate_governance_freeze(ROOT) == ()


def test_manifest_is_canonical_and_all_hashes_match():
    payload = _manifest()
    assert MANIFEST.read_bytes() == canonical_json_bytes(payload)
    for section in ("source_hashes", "child_manifest_hashes", "test_hashes", "frozen_evidence_hashes"):
        for relative, expected in payload[section].items():
            assert _sha(ROOT / relative) == expected, relative


def test_manifest_and_audit_inventory_are_complete():
    payload = _manifest()
    assert payload["activation_gate"] == "lcr_governance_baseline_frozen"
    assert payload["provider_requests_added"] == payload["network_requests_added"] == 0
    assert payload["production_hook_count"] == 1
    assert len(payload["capabilities"]) == 18
    assert payload["dependency_graph"] == {key: list(value) for key, value in dependency_graph(CAPABILITY_REGISTRY).items()}
    for relative in payload["audit_files"] + payload["test_files"] + payload["source_files"]:
        assert (ROOT / relative).is_file(), relative
    assert len(tuple(AUDIT_DIRECTORY.glob("LCR_BATCH110_*.json"))) == 12


def test_activation_gate_does_not_imply_active_integration():
    payload = _manifest()
    assert all(term not in payload["activation_gate"] for term in ("production_ready", "active_integration_ready", "rollout_ready"))
    boundaries = payload["production_boundaries"]
    assert boundaries == {
        "active_production_authorized": False,
        "automatic_rollout_authorized": False,
        "formal_output_replacement_authorized": False,
        "production_integration_authorized": False,
    }
