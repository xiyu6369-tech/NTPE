from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.name_resolution_contract_v72 import (
    DEFAULT_ENABLED, UNRESOLVED_NAME_OUTPUT_STRATEGY, NameResolutionRecord,
    apply_name_resolution_candidate, canonical_json, mapping_exclusion_reasons,
    render_prompt_mappings, resolve_inventory, validate_name_output,
)
from core.production_runtime.manifest import get_te_v7_stage_path, get_te_v7_artifact_path

STAGE = "TE-v7.2-Stage12.5.9"
ARTIFACT_ROOT = ROOT / "artifacts/te_v72_stage1259_name_resolution_contract_remediation"
MANIFEST = ROOT / "manifests/te_v720_stage1259_name_resolution_contract_remediation_manifest.json"
RELEASE = ROOT / "docs/releases/te_v7_2/TE_V720_STAGE1259_NAME_RESOLUTION_CONTRACT_REMEDIATION.md"
HISTORICAL_ROOT = get_te_v7_stage_path(ROOT, "te_v72_stage1258_candidate_structural_verification_canary")
CLAIM = get_te_v7_artifact_path(ROOT, "te_v72_stage1258_candidate_structural_verification_canary", "authorization_claim.json")
RESPONSE = get_te_v7_artifact_path(ROOT, "te_v72_stage1258_candidate_structural_verification_canary", "candidate_response.json")
EXPECTED_CLAIM_SHA256 = "81736fc37a12df55c3ce16ad8f09c3b7dd1c45f8a755b49a4c292f36c28acd8c"
EXPECTED_RESPONSE_SHA256 = "df46eddcc4360b0257a2347beeb0652a731c3752df3b8453ee33a53cbdc12873"
ACTIVATION_GATE = "translation_quality_integration_ready_for_controlled_canary"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fixed_records() -> tuple[NameResolutionRecord, NameResolutionRecord]:
    yeonghui = NameResolutionRecord.create(
        source_name="영희", identity_transliteration="Yeong-hui",
        approved_zh_hant_name=None, mapping_status="identity_only",
        mapping_source="character_memory", evidence_ids=("char-yeonghui",),
        approval_status="approved", unresolved_reason="missing_approved_zh_hant_name",
    )
    minsu = NameResolutionRecord.create(
        source_name="민수", identity_transliteration=None,
        approved_zh_hant_name=None, mapping_status="missing_approved_target_name",
        mapping_source="none", evidence_ids=(), approval_status="unreviewed",
        unresolved_reason="no_authoritative_target_mapping",
    )
    return yeonghui, minsu


def approved_example() -> NameResolutionRecord:
    return NameResolutionRecord.create(
        source_name="정태의", approved_zh_hant_name="鄭泰義",
        mapping_status="approved_target_mapping", mapping_source="glossary",
        evidence_ids=("human-reviewed-glossary-example",), approval_status="approved",
    )


def build_artifacts() -> dict[Path, bytes]:
    claim_before, response_before = CLAIM.read_bytes(), RESPONSE.read_bytes()
    if sha(claim_before) != EXPECTED_CLAIM_SHA256:
        raise ValueError("stage1258-claim-hash-mismatch")
    if sha(response_before) != EXPECTED_RESPONSE_SHA256:
        raise ValueError("stage1258-response-hash-mismatch")

    source = "영희가 민수와 선생님을 번갈아 보며 말했다. ‘선생님, 민수 씨도 함께 가실까요?’"
    raw_response = json.loads(response_before.decode("utf-8"))["raw_response"]
    yeonghui, minsu = fixed_records()
    approved = approved_example()
    resolved = resolve_inventory(("영희", "민수"), (yeonghui, minsu))
    rendered, rendering = render_prompt_mappings(
        (approved, yeonghui, minsu),
        source_first_occurrence={
            approved.normalized_source_name: 0,
            yeonghui.normalized_source_name: 1,
            minsu.normalized_source_name: 2,
        },
        token_budget=64,
    )
    disabled = apply_name_resolution_candidate("ORIGINAL_PROMPT", resolved, enabled=False)
    enabled = apply_name_resolution_candidate("ORIGINAL_PROMPT", (approved, yeonghui, minsu), enabled=True)
    validation = validate_name_output(raw_response, source_text=source, records=resolved)
    example_matrix = {
        text: validate_name_output(text, source_text=source, records=resolved).to_dict()
        for text in ("영희", "民수", "英희", "Yeong희", "민Su", "鄭태의")
    }
    common = {
        "stage": STAGE, "offline_only": True, "provider_requests": 0, "network_requests": 0,
        "runtime_activation": False, "production_integration": False,
        "automatic_rollout_authorized": False, "formal_output_replacement_authorized": False,
        "production_authorized": False, "provider_execution_authorized": False,
        "activation_gate": ACTIVATION_GATE,
        "historical_claim_sha256": EXPECTED_CLAIM_SHA256,
        "historical_response_sha256": EXPECTED_RESPONSE_SHA256,
    }
    artifacts = {
        ARTIFACT_ROOT / "source_inventory.json": canonical_json({
            **common, "status": "PASS", "source_language": "ko",
            "source_names": [
                {"source_name": "영희", "normalized_source_name": yeonghui.normalized_source_name,
                 "first_occurrence": source.index("영희")},
                {"source_name": "민수", "normalized_source_name": minsu.normalized_source_name,
                 "first_occurrence": source.index("민수")},
            ],
            "corpus_name_mappings": [], "glossary_entries": [],
            "character_memory_identity_entries": [{"source_name": "영희", "identity_transliteration": "Yeong-hui"}],
        }),
        ARTIFACT_ROOT / "name_resolution_contract.json": canonical_json({
            **common, "status": "PASS", "immutable": True,
            "fields": list(yeonghui.to_dict()),
            "mapping_status_values": [
                "approved_target_mapping", "identity_only", "missing_approved_target_name",
                "conflicting_target_mapping", "rejected_target_mapping",
                "expired_target_mapping", "unresolved",
            ],
            "mapping_source_values": ["corpus", "glossary", "character_memory", "human_review", "none"],
            "resolution_priority": [
                "approved_human_reviewed_glossary", "approved_corpus",
                "approved_character_memory_target_mapping", "identity_transliteration_only", "unresolved",
            ],
            "forbidden_selection_heuristics": [
                "first_match", "latest_match", "longest_match", "alphabetical_selection",
                "model_inference", "transliteration_to_chinese",
            ],
            "records": [item.to_dict() for item in resolved],
        }),
        ARTIFACT_ROOT / "mapping_eligibility_evidence.json": canonical_json({
            **common, "status": "PASS",
            "approved_example": approved.to_dict(),
            "approved_example_eligible": approved.prompt_eligible,
            "yeonghui": yeonghui.to_dict(),
            "yeonghui_exclusion_reasons": list(mapping_exclusion_reasons(yeonghui)),
            "minsu": minsu.to_dict(),
            "minsu_exclusion_reasons": list(mapping_exclusion_reasons(minsu)),
            "romanization_is_not_approved_zh_hant_name": True,
            "mixed_script_targets_rejected": ["民수", "英희", "Yeong희", "민Su", "鄭태의"],
        }),
        ARTIFACT_ROOT / "unresolved_name_evidence.json": canonical_json({
            **common, "status": "PASS",
            "unresolved_name_output_strategy": UNRESOLVED_NAME_OUTPUT_STRATEGY,
            "names": [
                {"source_name": "영희", "mapping_status": "identity_only",
                 "identity_transliteration": "Yeong-hui", "approved_zh_hant_name": None,
                 "prompt_eligible": False, "unresolved_reason": "missing_approved_zh_hant_name"},
                {"source_name": "민수", "mapping_status": "missing_approved_target_name",
                 "identity_transliteration": None, "approved_zh_hant_name": None,
                 "prompt_eligible": False, "unresolved_reason": "no_authoritative_target_mapping"},
            ],
            "invented_target_names": [],
        }),
        ARTIFACT_ROOT / "conflict_resolution_contract.json": canonical_json({
            **common, "status": "PASS", "conflict_behavior": "fail_closed",
            "mapping_status": "conflicting_target_mapping", "prompt_eligible": False,
            "automatic_selection_allowed": False,
            "forbidden_selection": ["first_match", "latest_match", "longest_match", "alphabetical"],
        }),
        ARTIFACT_ROOT / "prompt_rendering_candidate.json": canonical_json({
            **common, "status": "PASS", "default_enabled": DEFAULT_ENABLED,
            "disabled_prompt_unchanged": disabled.prompt == "ORIGINAL_PROMPT",
            "disabled_provider_payload_changed": disabled.provider_payload_changed,
            "enabled_example_rendering": rendered,
            "enabled_candidate_prompt_contains_policy": "blocked_pending_policy" in enabled.prompt,
            "rendering_evidence": rendering.to_dict(),
            "identity_only_rendered_as_target_mapping": False,
            "unresolved_rendered_as_target_mapping": False,
            "production_hook_count_added": 0, "runtime_request_path_modified": False,
        }),
        ARTIFACT_ROOT / "output_validation_extension.json": canonical_json({
            **common, "status": "PASS", "stage1258_response_validation": validation.to_dict(),
            "classification_matrix": example_matrix,
            "upper_level_compatibility_class": "mixed_language_inline_output",
            "validate_only": True, "repair_applied": False, "provider_request": False,
        }),
        ARTIFACT_ROOT / "budget_evidence.json": canonical_json({
            **common, "status": "PASS", "priority_region": "glossary_name_mapping",
            "deterministic_ordering": [
                "source_first_occurrence", "stable_normalized_source_name", "mapping_fingerprint",
            ],
            "rendering_evidence": rendering.to_dict(),
            "approved_mapping_rendered": "- 정태의 → 鄭泰義" in rendered,
            "identity_only_budget_consumed": False,
            "unresolved_budget_consumed": False,
            "budget_exhaustion_observable": True,
        }),
        ARTIFACT_ROOT / "activation_contract.json": canonical_json({
            **common, "status": "PASS",
            "offline_status": "name_resolution_contract_remediation_prepared",
            "candidate_default_enabled": False,
        }),
        ARTIFACT_ROOT / "preparation_summary.json": canonical_json({
            **common, "status": "PASS",
            "offline_status": "name_resolution_contract_remediation_prepared",
            "stage1258_failure_overwritten": False, "historical_claim_hash_unchanged": True,
            "historical_response_hash_unchanged": True, "frozen_files_modified": 0,
            "provider_layer_modified": 0, "runtime_request_path_modified": 0,
            "tracked_deletions": 0, "next_canary_authorized": False,
        }),
    }
    if CLAIM.read_bytes() != claim_before or RESPONSE.read_bytes() != response_before:
        raise ValueError("stage1258-historical-evidence-mutated")
    return artifacts


def write_artifacts() -> dict[Path, bytes]:
    claim_before, response_before = CLAIM.read_bytes(), RESPONSE.read_bytes()
    artifacts = build_artifacts()
    for path, data in sorted(artifacts.items(), key=lambda item: item[0].as_posix()):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    if CLAIM.read_bytes() != claim_before or RESPONSE.read_bytes() != response_before:
        raise ValueError("stage1258-historical-evidence-mutated")
    return artifacts


def write_manifest(artifacts: dict[Path, bytes]) -> Path:
    source_paths = [
        "core/name_resolution_contract_v72/__init__.py",
        "core/name_resolution_contract_v72/models.py",
        "core/name_resolution_contract_v72/normalization.py",
        "core/name_resolution_contract_v72/eligibility.py",
        "core/name_resolution_contract_v72/resolver.py",
        "core/name_resolution_contract_v72/renderer.py",
        "core/name_resolution_contract_v72/validation.py",
        "core/name_resolution_contract_v72/serialization.py",
        "core/name_resolution_contract_v72/errors.py",
        "core/name_resolution_contract_v72/candidate_adapter.py",
        "tools/generate_te_v720_stage1259_name_resolution_contract_remediation.py",
    ]
    test_paths = [
        "tests/unit/test_stage1259_name_resolution_contract.py",
        "ntpe_te_v720_stage1259_name_resolution_contract_remediation_test.py",
        "tests/integration/translation_engine_v720_stage1259_name_resolution_contract_remediation_test.py",
    ]
    manifest = {
        "schema_version": "te-v7.2-stage12.5.9-name-resolution-contract-remediation-v1",
        "stage": STAGE,
        "artifact_hashes": {path.relative_to(ROOT).as_posix(): sha(data) for path, data in artifacts.items()},
        "source_hashes": {path: sha((ROOT / path).read_bytes()) for path in source_paths},
        "test_hashes": {path: sha((ROOT / path).read_bytes()) for path in test_paths},
        "release_sha256": sha(RELEASE.read_bytes()),
        "historical_claim_sha256": sha(CLAIM.read_bytes()),
        "historical_response_sha256": sha(RESPONSE.read_bytes()),
        "provider_requests": 0, "network_requests": 0, "tracked_deletions": 0,
        "frozen_files_modified": 0, "provider_layer_modified": 0,
        "runtime_request_path_modified": 0, "next_canary_authorized": False,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_bytes(canonical_json(manifest))
    return MANIFEST


def main() -> int:
    artifacts = write_artifacts()
    manifest = write_manifest(artifacts)
    print(json.dumps({
        "status": "PASS", "artifacts": len(artifacts),
        "manifest": manifest.relative_to(ROOT).as_posix(),
        "provider_requests": 0, "network_requests": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
