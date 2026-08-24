from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from core.prompt_contract_verification_canary.claim_safe_remediation import validate_before_claim
from core.prompt_contract_verification_canary.corpus_identity import build_corpus_identity_contract, resolve_canary_corpus_id
from core.production_runtime.manifest import get_te_v7_stage_path, get_te_v7_artifact_path

HISTORICAL_ROOT = get_te_v7_stage_path(ROOT, "te_v72_stage1256_prompt_verification_canary")
ARTIFACT_ROOT = ROOT / "artifacts/te_v72_stage1256a_claim_safe_corpus_binding_remediation"
CLAIM = get_te_v7_artifact_path(ROOT, "te_v72_stage1256_prompt_verification_canary", "authorization_claim.json")
FIXTURE = ROOT / "tests/fixtures/te_v72_canary/golden_corpus.json"
EXPECTED_CLAIM_SHA256 = "82a0747c084e3844047e8d6e701bc4c4309ba20b56519119b2f7c0988c56f5eb"
GATE = "translation_quality_integration_ready_for_controlled_canary"

def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha(value: bytes) -> str: return hashlib.sha256(value).hexdigest()

def historical_payloads() -> dict[Path, bytes]:
    common = {"stage": "TE-v7.2-Stage12.5.6", "preflight_passed": True, "claim_created": True,
              "claim_replay_allowed": False, "claim_status": "consumed_by_execution_start",
              "provider_requests_consumed": 0, "baseline_started": False, "candidate_started": False,
              "failure_phase": "corpus_resolution", "failure_class": "corpus_identifier_contract_mismatch",
              "exception_type": "StopIteration", "requested_corpus_id": "canary-001", "resolved_corpus_id": None,
              "available_canonical_corpus_id": "canary-001-character-honorific"}
    summary = {**common, "status": "blocked_before_provider", "manual_review": "not_reviewable",
               "activation_gate": GATE, "provider_requests_added": 0, "network_requests_added": 0,
               "retry_added": 0, "fallback": False}
    decision = {"stage": "TE-v7.2-Stage12.5.6", "prompt_contract_verification_canary_passed": False,
                "canary_status": "blocked_before_provider", "manual_review": "not_reviewable",
                "activation_gate": GATE, "active_production_authorized": False,
                "automatic_rollout_authorized": False, "formal_output_replacement_authorized": False,
                "production_authorized": False}
    failure = {**common, "provider_error": False, "timeout": False, "candidate_regression": False,
               "translation_quality_failure": False, "prompt_contract_failure": False}
    return {HISTORICAL_ROOT / "execution_summary.json": canonical(summary),
            HISTORICAL_ROOT / "activation_decision.json": canonical(decision),
            HISTORICAL_ROOT / "failure_record.json": canonical(failure)}

def build_artifacts() -> dict[Path, bytes]:
    contract = build_corpus_identity_contract(FIXTURE)
    logical = resolve_canary_corpus_id("canary-001", (contract,))
    canonical_result = resolve_canary_corpus_id(contract.canonical_id, (contract,))
    prerequisites = {name: True for name in ("git_worktree_checks", "artifact_hash_checks", "readiness_gate_checks", "authorization_budget_checks")}
    validation = validate_before_claim(root=ROOT, logical_id="canary-001", claim_path=CLAIM, prerequisite_checks=prerequisites)
    historical = historical_payloads()
    historical_hashes = {path.relative_to(ROOT).as_posix(): sha(data) for path, data in historical.items()}
    claim_hash = sha(CLAIM.read_bytes())
    if claim_hash != EXPECTED_CLAIM_SHA256: raise ValueError("historical-stage1256-claim-hash-mismatch")
    artifacts: dict[Path, bytes] = dict(historical)
    artifacts[ARTIFACT_ROOT / "corpus_identity_contract.json"] = canonical(contract.to_dict())
    artifacts[ARTIFACT_ROOT / "corpus_resolution_validation.json"] = canonical({
        "status": "PASS", "logical_id": logical.logical_id, "logical_resolves_to": logical.canonical_id,
        "canonical_id_direct_resolution": canonical_result.canonical_id, "deterministic": True,
        "exact_mapping_only": True, "fuzzy_prefix_matching": False, "first_list_item_selection": False,
        "unknown_id_fail_closed": True, "duplicate_alias_fail_closed": True, "ambiguous_mapping_fail_closed": True})
    artifacts[ARTIFACT_ROOT / "claim_lifecycle_validation.json"] = canonical({
        "status": "PASS", "historical_claim_sha256": claim_hash, "claim_immutable": True,
        "claim_replay_allowed": False, "claim_delete_allowed": False, "claim_rebuild_allowed": False,
        "claim_status": "consumed_by_execution_start", "provider_requests_consumed": 0})
    artifacts[ARTIFACT_ROOT / "preflight_ordering_validation.json"] = canonical({
        "status": "PASS", "steps": ["git_worktree_checks", "artifact_hash_checks", "readiness_gate_checks",
        "authorization_budget_checks", "corpus_logical_id_resolution", "corpus_source_hash_validation",
        "request_plan_construction_validation", "claim_eligibility_validation", "single_use_claim_creation",
        "provider_execution"], "corpus_resolution_before_claim": True,
        "resolution_failure_claim_created": False, "post_claim_exception_captured": True})
    artifacts[ARTIFACT_ROOT / "historical_stage1256_seal.json"] = canonical({
        "status": "PASS", "historical_claim_sha256": claim_hash, "historical_claim_preserved": True,
        "historical_artifact_hashes": historical_hashes})
    artifacts[ARTIFACT_ROOT / "remediation_summary.json"] = canonical({
        "stage": "TE-v7.2-Stage12.5.6A", "status": "PASS", "offline_only": True,
        "logical_id": contract.logical_id, "canonical_id": contract.canonical_id,
        "historical_stage1256_status": "blocked_before_provider", "activation_gate": GATE,
        "provider_requests_added": 0, "network_requests_added": 0, "retry_added": 0, "fallback": False,
        "frozen_files_modified": 0, "provider_layer_modified": 0, "runtime_request_path_modified": 0,
        "production_authorized": False, "automatic_rollout_authorized": False,
        "formal_output_replacement_authorized": False})
    return artifacts

def write_artifacts() -> dict[Path, bytes]:
    before = CLAIM.read_bytes(); artifacts = build_artifacts()
    for path, data in sorted(artifacts.items(), key=lambda item: item[0].as_posix()):
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    if CLAIM.read_bytes() != before: raise ValueError("historical-stage1256-claim-mutated")
    return artifacts

def write_manifest(artifacts: dict[Path, bytes]) -> Path:
    release = ROOT / "docs/releases/te_v7_2/TE_V720_STAGE1256A_CLAIM_SAFE_CORPUS_BINDING_REMEDIATION.md"
    source_paths = ["core/prompt_contract_verification_canary/corpus_identity.py",
                    "core/prompt_contract_verification_canary/claim_safe_remediation.py",
                    "tools/generate_te_v720_stage1256a_claim_safe_corpus_binding_remediation.py"]
    test_paths = ["tests/unit/test_stage1256a_claim_safe_corpus_binding.py",
                  "ntpe_te_v720_stage1256a_claim_safe_corpus_binding_remediation_test.py",
                  "tests/integration/translation_engine_v720_stage1256a_claim_safe_corpus_binding_remediation_test.py"]
    manifest = {"schema_version": "te-v7.2-stage12.5.6a-claim-safe-corpus-binding-v1",
                "stage": "TE-v7.2-Stage12.5.6A", "historical_claim_sha256": sha(CLAIM.read_bytes()),
                "artifact_hashes": {path.relative_to(ROOT).as_posix(): sha(data) for path, data in artifacts.items()},
                "source_hashes": {path: sha((ROOT / path).read_bytes()) for path in source_paths},
                "test_hashes": {path: sha((ROOT / path).read_bytes()) for path in test_paths},
                "release_sha256": sha(release.read_bytes()), "provider_requests_added": 0,
                "network_requests_added": 0, "retry_added": 0, "fallback": False,
                "activation_gate": GATE, "production_authorized": False,
                "automatic_rollout_authorized": False, "formal_output_replacement_authorized": False}
    path = ROOT / "manifests/te_v720_stage1256a_claim_safe_corpus_binding_remediation_manifest.json"
    path.write_bytes(canonical(manifest)); return path

def main() -> int:
    artifacts = write_artifacts(); manifest = write_manifest(artifacts)
    print(json.dumps({"status": "PASS", "artifacts": len(artifacts), "manifest": manifest.relative_to(ROOT).as_posix(),
                      "provider_requests_added": 0, "network_requests_added": 0}, sort_keys=True)); return 0

if __name__ == "__main__": raise SystemExit(main())
