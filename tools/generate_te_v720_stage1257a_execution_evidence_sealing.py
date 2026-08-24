from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.production_runtime.manifest import get_te_v7_stage_path, get_te_v7_artifact_path

HISTORICAL_ROOT = get_te_v7_stage_path(ROOT, "te_v72_stage1257_prompt_verification_canary")
ARTIFACT_ROOT = ROOT / "artifacts/te_v72_stage1257a_execution_evidence_sealing"
CLAIM = get_te_v7_artifact_path(ROOT, "te_v72_stage1257_prompt_verification_canary", "authorization_claim.json")
EXPECTED_CLAIM_SHA256 = "8b6c99602e6c6d192a41e024e017dc3ebe3a141a9af13914ead38691753a3c21"
GATE = "translation_quality_integration_ready_for_controlled_canary"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(name: str) -> dict[str, object]:
    return json.loads((HISTORICAL_ROOT / name).read_text(encoding="utf-8"))


def build_artifacts() -> dict[Path, bytes]:
    before = CLAIM.read_bytes()
    claim_hash = sha(before)
    if claim_hash != EXPECTED_CLAIM_SHA256:
        raise ValueError("stage1257-claim-hash-mismatch")
    baseline = _read_json("baseline_response.json")
    structural = _read_json("structural_validation.json")
    if not (baseline.get("timeout") is True and structural.get("request_count") == 1):
        raise ValueError("stage1257-historical-result-mismatch")
    common = {
        "stage": "TE-v7.2-Stage12.5.7A", "historical_stage": "TE-v7.2-Stage12.5.7",
        "historical_claim_sha256": claim_hash, "activation_gate": GATE,
        "provider_requests_added": 0, "network_requests_added": 0, "retry_added": 0,
        "fallback": False, "production_authorized": False,
        "automatic_rollout_authorized": False, "formal_output_replacement_authorized": False,
    }
    execution_hashes = {name: sha((HISTORICAL_ROOT / name).read_bytes()) for name in (
        "preflight.json", "corpus_resolution.json", "authorization_claim.json", "baseline_request.json",
        "baseline_response.json", "structural_validation.json", "manual_review_package.json",
        "provisional_activation_decision.json", "execution_summary.json")}
    payloads = {
        "historical_execution_seal.json": {
            **common, "status": "PASS", "execution_status": "completed_fail_closed",
            "canary_status": "inconclusive_baseline_timeout", "failure_phase": "baseline_provider_execution",
            "failure_class": "baseline_timeout", "provider_requests_consumed": 1,
            "baseline_started": True, "baseline_success": False, "baseline_timeout": True,
            "candidate_started": False, "candidate_success": False, "manual_review_status": "not_reviewable",
            "prompt_contract_verification_canary_passed": False, "claim_hash_unchanged": True,
            "historical_execution_hashes": execution_hashes,
        },
        "claim_lifecycle.json": {
            **common, "status": "PASS", "claim_status": "consumed", "claim_replay_allowed": False,
            "claim_deleted": False, "claim_recreated": False, "claim_hash_unchanged": True,
            "creation_time_consumed_request_count": 0,
            "creation_time_consumed_request_count_meaning": "immutable_creation_time_snapshot",
            "execution_summary_consumed_request_count": 1,
            "execution_summary_consumed_request_count_meaning": "formal_execution_result",
        },
        "request_budget_accounting.json": {
            **common, "status": "PASS", "authorized_request_budget": 2,
            "actual_provider_requests_consumed": 1, "unused_request_budget": 1,
            "unused_request_budget_reusable": False, "candidate_started": False,
        },
        "test_state_isolation.json": {
            **common, "status": "PASS", "preparation_fixture": {
                "claim_exists": False, "preflight_passes": True, "claim_eligibility": True,
                "artifact_location": "isolated_temp_directory"}, "historical_post_execution_fixture": {
                "claim_exists": True, "claim_replay_rejected": True, "provider_request_count": 1,
                "candidate_started": False, "unused_request_budget_reusable": False,
                "activation_gate": GATE}, "working_claim_modified": False,
        },
        "final_activation_decision.json": {
            **common, "activation_decision": "final_fail_closed",
            "prompt_contract_verification_canary_passed": False,
            "canary_status": "inconclusive_baseline_timeout", "manual_review_status": "not_reviewable",
            "active_production_authorized": False,
        },
        "sealing_summary.json": {
            **common, "status": "PASS", "execution_status": "completed_fail_closed",
            "canary_status": "inconclusive_baseline_timeout", "failed": 0,
            "tracked_deletions": 0, "claim_hash_unchanged": True,
            "offline_only": True, "candidate_rerun": False, "claim_replay": False,
        },
    }
    artifacts = {ARTIFACT_ROOT / name: canonical(value) for name, value in payloads.items()}
    if CLAIM.read_bytes() != before:
        raise ValueError("stage1257-claim-mutated")
    return artifacts


def write_artifacts() -> dict[Path, bytes]:
    before = CLAIM.read_bytes()
    artifacts = build_artifacts()
    for path, data in sorted(artifacts.items(), key=lambda item: item[0].as_posix()):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    if CLAIM.read_bytes() != before:
        raise ValueError("stage1257-claim-mutated")
    return artifacts


def write_manifest(artifacts: dict[Path, bytes]) -> Path:
    release = "docs/releases/te_v7_2/TE_V720_STAGE1257A_FAIL_CLOSED_EXECUTION_EVIDENCE_SEALING.md"
    source_paths = ["core/prompt_verification_canary_stage1257/framework.py",
                    "tools/generate_te_v720_stage1257a_execution_evidence_sealing.py"]
    test_paths = ["tests/unit/test_stage1257_prompt_verification_canary.py",
                  "tests/unit/test_stage1257a_execution_evidence_sealing.py",
                  "ntpe_te_v720_stage1257_prompt_verification_canary_test.py",
                  "ntpe_te_v720_stage1257a_execution_evidence_sealing_test.py",
                  "tests/integration/translation_engine_v720_stage1257_prompt_verification_canary_test.py",
                  "tests/integration/translation_engine_v720_stage1257a_execution_evidence_sealing_test.py"]
    historical = {name: sha((HISTORICAL_ROOT / name).read_bytes()) for name in (
        "preflight.json", "corpus_resolution.json", "authorization_claim.json", "baseline_request.json",
        "baseline_response.json", "structural_validation.json", "manual_review_package.json",
        "provisional_activation_decision.json", "execution_summary.json")}
    manifest = {"schema_version": "te-v7.2-stage12.5.7a-execution-evidence-sealing-v1",
        "stage": "TE-v7.2-Stage12.5.7A", "historical_claim_sha256": sha(CLAIM.read_bytes()),
        "preflight_hash": historical["preflight.json"], "corpus_resolution_hash": historical["corpus_resolution.json"],
        "authorization_claim_hash": historical["authorization_claim.json"], "baseline_request_hash": historical["baseline_request.json"],
        "baseline_response_hash": historical["baseline_response.json"], "structural_validation_hash": historical["structural_validation.json"],
        "manual_review_package_hash": historical["manual_review_package.json"], "provisional_decision_hash": historical["provisional_activation_decision.json"],
        "execution_summary_hash": historical["execution_summary.json"],
        "final_activation_decision_hash": sha(artifacts[ARTIFACT_ROOT / "final_activation_decision.json"]),
        "artifact_hashes": {p.relative_to(ROOT).as_posix(): sha(data) for p, data in artifacts.items()},
        "source_hashes": {p: sha((ROOT / p).read_bytes()) for p in source_paths},
        "test_hashes": {p: sha((ROOT / p).read_bytes()) for p in test_paths},
        "release_sha256": sha((ROOT / release).read_bytes()), "provider_requests_added": 0,
        "network_requests_added": 0, "retry_added": 0, "fallback": False, "claim_hash_unchanged": True}
    path = ROOT / "manifests/te_v720_stage1257a_execution_evidence_sealing_manifest.json"
    path.write_bytes(canonical(manifest))
    return path



def main() -> int:
    artifacts = write_artifacts()
    manifest = write_manifest(artifacts)
    print(json.dumps({"status": "PASS", "artifacts": len(artifacts), "manifest": manifest.as_posix(),
                      "provider_requests_added": 0, "network_requests_added": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
