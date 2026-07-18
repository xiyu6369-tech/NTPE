from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path

import pytest

from core.lcr_governance_baseline_consumption import (
    INVALID,
    REJECTED,
    GovernanceBaselineInvalidError,
    audit_governance_baseline_consumption,
    load_governance_baseline,
    validate_authorization_state,
    validate_capability_registry,
    validate_claim_payload,
    validate_dependency_graph,
    validate_taxonomy_payload,
    verify_governance_baseline,
)
from core.lcr_governance_baseline_consumption.loader import resolve_allowed_file
from core.shared.evidence import canonical_json_bytes


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def baseline():
    return load_governance_baseline(ROOT)


def test_valid_baseline_is_loaded(baseline):
    reference, payload = baseline
    assert reference.batch_id == payload["batch"] == "11.0"
    assert reference.activation_gate == "lcr_governance_baseline_frozen"


def test_source_manifest_hash_mismatch_is_rejected(monkeypatch):
    import core.lcr_governance_baseline_consumption.loader as loader
    monkeypatch.setattr(loader, "EXPECTED_SOURCE_MANIFEST_SHA256", "0" * 64)
    result = audit_governance_baseline_consumption(ROOT)
    assert result.status == REJECTED
    assert result.violations == ("source_manifest_hash_mismatch",)


def test_child_manifest_hash_mismatch_is_rejected(baseline):
    reference, payload = baseline
    hashes = dict(reference.child_manifest_hashes)
    first = next(iter(hashes))
    hashes[first] = "0" * 64
    violations, _ = verify_governance_baseline(replace(reference, child_manifest_hashes=hashes), payload, ROOT)
    assert f"child_manifest_hash_mismatch:{first}" in violations


def test_missing_capability_is_rejected(baseline):
    _, payload = baseline
    assert "capability_count_changed" in validate_capability_registry(payload["capabilities"][:-1])


def test_duplicate_capability_is_rejected(baseline):
    _, payload = baseline
    capabilities = [dict(item) for item in payload["capabilities"]]
    capabilities[-1]["capability_id"] = capabilities[0]["capability_id"]
    assert "duplicate_capability_id" in validate_capability_registry(capabilities)


def test_capability_records_are_immutable_and_read_only(baseline):
    reference, _ = baseline
    with pytest.raises(FrozenInstanceError):
        reference.batch_id = "11.1"
    with pytest.raises(TypeError):
        reference.child_manifest_hashes["new"] = "bad"


def test_missing_dependency_is_rejected(baseline):
    _, payload = baseline
    graph = {key: list(value) for key, value in payload["dependency_graph"].items()}
    graph["character_memory_v2"] = ["missing"]
    assert any(item.startswith("orphan_dependency") for item in validate_dependency_graph(graph, set(graph)))


def test_dependency_cycle_is_rejected(baseline):
    _, payload = baseline
    graph = {key: list(value) for key, value in payload["dependency_graph"].items()}
    graph["character_memory_v2"] = ["context_scene_memory"]
    assert "dependency_cycle" in validate_dependency_graph(graph, set(graph))


def test_self_dependency_is_rejected(baseline):
    _, payload = baseline
    graph = {key: list(value) for key, value in payload["dependency_graph"].items()}
    graph["character_memory_v2"] = ["character_memory_v2"]
    assert "self_dependency:character_memory_v2" in validate_dependency_graph(graph, set(graph))


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("failure_type_count", 18, "taxonomy_count_changed"),
        ("failure_types_added", 1, "taxonomy_addition_detected"),
        ("classification_semantics_modified", True, "taxonomy_semantics_changed"),
        ("deterministic", False, "taxonomy_not_deterministic"),
    ],
)
def test_taxonomy_drift_is_rejected(field, value, code):
    payload = {
        "failure_type_count": 19,
        "failure_types_added": 0,
        "classification_semantics_modified": False,
        "deterministic": True,
    }
    payload[field] = value
    assert code in validate_taxonomy_payload(payload)


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"authorization_consumed": False}, "claim_not_consumed"),
        ({"additional_execution_allowed": True}, "claim_replay_allowed"),
        ({"response_status_classification": "success"}, "claim_outcome_changed"),
        ({"formal_output_changed": True}, "claim_production_state_changed"),
    ],
)
def test_claim_replay_or_drift_is_rejected(change, code):
    payload = {
        "authorization_consumed": True,
        "additional_execution_allowed": False,
        "response_status_classification": "timeout",
        "formal_output_changed": False,
        "resume_changed": False,
        "cache_changed": False,
        "character_store_changed": False,
        "context_store_changed": False,
    }
    payload.update(change)
    assert code in validate_claim_payload(payload)


@pytest.mark.parametrize("frozen", [0, 2])
def test_hook_count_other_than_one_is_rejected(baseline, frozen):
    reference, payload = baseline
    violations, _ = verify_governance_baseline(replace(reference, production_hook_count=frozen), payload, ROOT)
    assert "production_hook_count_changed" in violations


def test_authorization_missing_field_is_invalid():
    assert validate_authorization_state({"active_production_authorized": False}) == ("authorization_schema_invalid",)


def test_authorization_wrong_type_is_rejected():
    state = {
        "active_production_authorized": 0,
        "automatic_rollout_authorized": False,
        "production_integration_authorized": False,
        "formal_output_replacement_authorized": False,
    }
    assert "authorization_relaxed:active_production_authorized" in validate_authorization_state(state)


@pytest.mark.parametrize(
    "field",
    [
        "active_production_authorized",
        "automatic_rollout_authorized",
        "production_integration_authorized",
        "formal_output_replacement_authorized",
    ],
)
def test_any_true_authorization_is_rejected(field):
    state = {name: False for name in (
        "active_production_authorized", "automatic_rollout_authorized",
        "production_integration_authorized", "formal_output_replacement_authorized",
    )}
    state[field] = True
    assert validate_authorization_state(state) == (f"authorization_relaxed:{field}",)


def test_path_traversal_is_rejected():
    with pytest.raises(GovernanceBaselineInvalidError, match="path_traversal_rejected"):
        resolve_allowed_file(ROOT, "../outside.json")


def test_symlink_component_is_rejected(tmp_path, monkeypatch):
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda self: self.name == "link" or original(self))
    with pytest.raises(GovernanceBaselineInvalidError, match="symlink_escape_rejected"):
        resolve_allowed_file(tmp_path, "link/target.json")


def test_source_manifest_is_canonical():
    path = ROOT / "manifests/lcr_batch110_governance_freeze_manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path.read_bytes() == canonical_json_bytes(payload)


def test_three_reads_are_byte_identical_and_ordered():
    outputs = [canonical_json_bytes(audit_governance_baseline_consumption(ROOT).to_dict()) for _ in range(3)]
    assert outputs[0] == outputs[1] == outputs[2]


def test_violations_are_deterministically_sorted(baseline):
    reference, payload = baseline
    bad = replace(reference, production_hook_count=2, authorization_state={
        "active_production_authorized": True,
        "automatic_rollout_authorized": False,
        "production_integration_authorized": False,
        "formal_output_replacement_authorized": False,
    })
    violations, _ = verify_governance_baseline(bad, payload, ROOT)
    assert violations == tuple(sorted(violations))


def test_alternate_manifest_is_never_used():
    result = audit_governance_baseline_consumption(ROOT, "manifests/other.json")
    assert result.status == INVALID
    assert result.violations == ("alternate_source_manifest_rejected",)
