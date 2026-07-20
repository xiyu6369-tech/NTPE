from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.prompt_contract_verification_canary.candidate_structural_canary import (
    ARTIFACT_DIR, CANONICAL_ID, FIXTURE_HASH, FORBIDDEN_LABELS, LOGICAL_ID, MODEL,
    PASS_GATE, PREPARATION_STEPS, PROVIDER, READY_GATE, SOURCE_HASH, STAGE_ID,
    build_candidate_request_plan, canonical, public_request_plan, sha,
)

ARTIFACT_ROOT = ROOT / ARTIFACT_DIR
MANIFEST_PATH = ROOT / "manifests/te_v720_stage1258_candidate_structural_verification_canary_manifest.json"
RELEASE_PATH = ROOT / "docs/releases/te_v7_2/TE_V720_STAGE1258_CANDIDATE_STRUCTURAL_VERIFICATION_CANARY.md"
HISTORICAL_CLAIMS = (
    ROOT / "artifacts/te_v72_stage1256_prompt_verification_canary/authorization_claim.json",
    ROOT / "artifacts/te_v72_stage1257_prompt_verification_canary/authorization_claim.json",
)


def build_preparation_artifacts() -> dict[Path, bytes]:
    historical_before = {path: path.read_bytes() for path in HISTORICAL_CLAIMS}
    plan = build_candidate_request_plan(ROOT)
    public_plan = public_request_plan(plan)
    structural_checks = {
        "provider_execution": ["success", "timeout", "error_category", "elapsed_seconds", "raw_response_presence"],
        "source_echo": ["exact_source_echo", "normalized_source_echo", "partial_source_sequence",
                        "hangul_character_count", "hangul_ratio"],
        "forbidden_labels": list(FORBIDDEN_LABELS),
        "output_wrappers": ["markdown_code_fence", "json_wrapper", "xml_wrapper", "explanation",
                            "summary", "translator_note", "bilingual_layout"],
        "completeness": ["non_empty", "minimum_output_length", "source_output_length_ratio",
                         "terminal_truncation", "complete_source_duplication", "repeated_output_block",
                         "malformed_fragment"],
        "target": ["traditional_chinese_signal", "dialogue_symbol_observation", "raw_response_immutable"],
    }
    claim_fields = [
        "stage_id", "provider", "model", "logical_corpus_id", "canonical_corpus_id",
        "authorized_request_budget", "attempts", "retry_allowed", "fallback_allowed",
        "automatic_rerun_allowed", "single_use", "replay_allowed", "request_plan_fingerprint",
        "prompt_fingerprint", "creation_timestamp_epoch_seconds", "authorization_scope_hash",
    ]
    artifacts = {
        ARTIFACT_ROOT / "preparation_summary.json": canonical({
            "stage": STAGE_ID, "status": "PASS", "mode": "offline_preparation",
            "candidate_only": True, "baseline_included": False, "quality_improvement_claimed": False,
            "provider_requests": 0, "network_requests": 0, "formal_execution_authorized": False,
            "formal_execution_performed": False, "execution_claim_created": False,
            "historical_claims_replayed": False, "unused_historical_budget_reused": False,
            "active_production_authorized": False, "automatic_rollout_authorized": False,
            "formal_output_replacement_authorized": False, "production_authorized": False,
        }),
        ARTIFACT_ROOT / "preflight_template.json": canonical({
            "stage": STAGE_ID,
            "ordered_steps": [{"ordinal": i + 1, "name": name} for i, name in enumerate(PREPARATION_STEPS)] + [
                {"ordinal": 14, "name": "create_single_use_claim"},
                {"ordinal": 15, "name": "candidate_provider_request"},
            ],
            "failure_through_step_13": {"claim_created": False, "provider_requests": 0, "fail_closed": True},
        }),
        ARTIFACT_ROOT / "corpus_resolution.json": canonical({
            "status": "PASS", "resolver": "stage1256a_exact_resolver", "logical_id": LOGICAL_ID,
            "canonical_id": CANONICAL_ID, "source_sha256": SOURCE_HASH, "fixture_sha256": FIXTURE_HASH,
            "prefix_matching": False, "alternate_corpus": False, "first_item_selection": False,
            "raw_next_stop_iteration": False, "resolved_before_claim": True,
        }),
        ARTIFACT_ROOT / "request_plan.json": canonical({
            **public_plan, "baseline_included": False, "maximum_provider_requests": 1,
            "timeout_seconds": 180, "parallelism": 1, "cross_provider_fallback": False,
            "formal_execution_authorized": False,
        }),
        ARTIFACT_ROOT / "structural_validation_contract.json": canonical({
            "stage": STAGE_ID, "checks": structural_checks,
            "allowed_results": ["candidate_structural_verified", "candidate_structural_failed",
                                "inconclusive_provider_timeout", "inconclusive_provider_error",
                                "blocked_before_provider"],
            "candidate_improved_is_out_of_scope": True, "translation_quality_is_out_of_scope": True,
        }),
        ARTIFACT_ROOT / "claim_contract.json": canonical({
            "stage": STAGE_ID, "claim_fields": claim_fields, "authorized_request_budget": 1,
            "attempts": 1, "retry_allowed": False, "fallback_allowed": False,
            "automatic_rerun_allowed": False, "single_use": True, "replay_allowed": False,
            "claim_created_during_preparation": False, "historical_claim_reuse_allowed": False,
            "claim_after_creation_delete_allowed": False, "claim_after_creation_overwrite_allowed": False,
        }),
        ARTIFACT_ROOT / "activation_contract.json": canonical({
            "stage": STAGE_ID, "gate_before_execution": READY_GATE,
            "maximum_gate_on_structural_pass": PASS_GATE,
            "gate_on_timeout_error_or_structural_failure": READY_GATE,
            "active_production_authorized": False, "automatic_rollout_authorized": False,
            "formal_output_replacement_authorized": False, "production_authorized": False,
            "candidate_improved": None, "translation_quality_passed": None,
        }),
    }
    if any(path.read_bytes() != before for path, before in historical_before.items()):
        raise ValueError("historical-claim-mutated")
    return artifacts


def write_artifacts() -> dict[Path, bytes]:
    artifacts = build_preparation_artifacts()
    for path, data in sorted(artifacts.items(), key=lambda item: item[0].as_posix()):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return artifacts


def write_manifest(artifacts: dict[Path, bytes]) -> Path:
    source_paths = [
        "core/prompt_contract_verification_canary/candidate_structural_canary.py",
        "tools/generate_te_v720_stage1258_candidate_structural_verification_canary.py",
        "tools/run_te_v720_stage1258_candidate_structural_verification_canary.py",
    ]
    test_paths = [
        "tests/unit/test_stage1258_candidate_structural_verification_canary.py",
        "ntpe_te_v720_stage1258_candidate_structural_verification_canary_test.py",
        "tests/integration/translation_engine_v720_stage1258_candidate_structural_verification_canary_test.py",
    ]
    manifest = {
        "schema_version": "te-v7.2-stage12.5.8-candidate-structural-verification-preparation-v1",
        "stage": STAGE_ID, "mode": "offline_preparation",
        "artifact_hashes": {path.relative_to(ROOT).as_posix(): sha(data) for path, data in artifacts.items()},
        "source_hashes": {path: sha((ROOT / path).read_bytes()) for path in source_paths},
        "test_hashes": {path: sha((ROOT / path).read_bytes()) for path in test_paths},
        "release_sha256": sha(RELEASE_PATH.read_bytes()),
        "stage1256_claim_sha256": sha(HISTORICAL_CLAIMS[0].read_bytes()),
        "stage1257_claim_sha256": sha(HISTORICAL_CLAIMS[1].read_bytes()),
        "provider_requests": 0, "network_requests": 0, "tracked_deletions": 0,
        "frozen_files_modified": 0, "provider_layer_modified": 0, "runtime_request_path_modified": 0,
        "formal_execution_authorized": False,
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_bytes(canonical(manifest))
    return MANIFEST_PATH


def main() -> int:
    artifacts = write_artifacts()
    manifest = write_manifest(artifacts)
    print(json.dumps({
        "status": "PASS", "artifacts": len(artifacts), "manifest": manifest.relative_to(ROOT).as_posix(),
        "provider_requests": 0, "network_requests": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
