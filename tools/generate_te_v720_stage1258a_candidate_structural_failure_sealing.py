from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.prompt_contract_verification_canary.candidate_structural_canary import (
    READY_GATE, build_candidate_request_plan,
)

STAGE = "TE-v7.2-Stage12.5.8A"
HISTORICAL_ROOT = ROOT / "artifacts/te_v72_stage1258_candidate_structural_verification_canary"
ARTIFACT_ROOT = ROOT / "artifacts/te_v72_stage1258a_candidate_structural_failure_sealing"
CLAIM = HISTORICAL_ROOT / "authorization_claim.json"
RESPONSE = HISTORICAL_ROOT / "candidate_response.json"
EXPECTED_CLAIM_SHA256 = "81736fc37a12df55c3ce16ad8f09c3b7dd1c45f8a755b49a4c292f36c28acd8c"
EXPECTED_RESPONSE_SHA256 = "df46eddcc4360b0257a2347beeb0652a731c3752df3b8453ee33a53cbdc12873"
PREPARATION_MANIFEST = ROOT / "manifests/te_v720_stage1258_candidate_structural_verification_canary_manifest.json"
MANIFEST = ROOT / "manifests/te_v720_stage1258_execution_manifest.json"
RELEASE = ROOT / "docs/releases/te_v7_2/TE_V720_STAGE1258A_CANDIDATE_STRUCTURAL_FAILURE_SEALING.md"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def classify_hangul_residuals(source: str, output: str) -> dict[str, object]:
    residuals = re.findall(r"[\uac00-\ud7a3\u1100-\u11ff]+", output)
    full_names = [name for name in ("영희", "민수") if name in output]
    partial_syllables = [
        residual for residual in residuals
        if residual not in full_names and any(residual in name for name in ("영희", "민수"))
    ]
    return {
        "observed_residuals": residuals,
        "full_korean_names_detected": full_names,
        "partial_korean_syllable_residuals": partial_syllables,
        "full_korean_source_echo": source.strip() in output,
        "partial_korean_source_echo": False,
        "korean_lexical_or_source_passage_echo": False,
        "hangul_proper_name_residual": bool(residuals),
        "inline_mixed_language_output": bool(residuals and re.search(r"[\u4e00-\u9fff]", output)),
    }


def _json(name: str) -> dict[str, object]:
    return json.loads((HISTORICAL_ROOT / name).read_text(encoding="utf-8"))


def build_artifacts() -> dict[Path, bytes]:
    claim_before = CLAIM.read_bytes()
    response_before = RESPONSE.read_bytes()
    if sha(claim_before) != EXPECTED_CLAIM_SHA256:
        raise ValueError("stage1258-claim-hash-mismatch")
    if sha(response_before) != EXPECTED_RESPONSE_SHA256:
        raise ValueError("stage1258-response-hash-mismatch")

    response = json.loads(response_before.decode("utf-8"))
    summary = _json("execution_summary.json")
    decision = _json("final_activation_decision.json")
    plan = build_candidate_request_plan(ROOT)
    prompt = str(plan["candidate_prompt"])
    source = str(plan["source"])
    trace = classify_hangul_residuals(source, str(response["raw_response"]))
    metadata = dict(plan["metadata"])

    if response.get("provider_success") is not True or response.get("timeout") is not False:
        raise ValueError("stage1258-provider-result-mismatch")
    if response.get("failures") != ["hangul_residual", "bilingual_layout"]:
        raise ValueError("stage1258-failure-reasons-mismatch")
    if summary.get("provider_requests") != 1 or decision.get("activation_gate") != READY_GATE:
        raise ValueError("stage1258-execution-summary-mismatch")
    if trace["observed_residuals"] != ["영희", "수"]:
        raise ValueError("stage1258-residual-evidence-mismatch")

    common = {
        "stage": STAGE, "historical_stage": "TE-v7.2-Stage12.5.8",
        "provider_requests_added": 0, "network_requests_added": 0,
        "retry_added": 0, "fallback": False, "activation_gate": READY_GATE,
        "claim_sha256": EXPECTED_CLAIM_SHA256, "response_sha256": EXPECTED_RESPONSE_SHA256,
        "active_production_authorized": False, "automatic_rollout_authorized": False,
        "formal_output_replacement_authorized": False, "production_authorized": False,
    }
    selected_character_entries = [{
        "record_id": "char-yeonghui", "source_name": "영희",
        "formal_mapping": "Yeong-hui", "selected": True, "present_in_prompt": True,
    }]
    name_evidence = [
        {
            "source_name": "영희", "corpus_mapping": None, "glossary_mapping": None,
            "character_memory_mapping": "Yeong-hui", "selected_character_memory_entry": "char-yeonghui",
            "rendered_prompt_mapping": "Yeong-hui", "mapping_present_in_prompt": True,
            "mapping_omitted_by_budget": False, "raw_response_residual": "영희",
            "expected_target_representation": "Yeong-hui", "unresolved": False,
            "evidence_class": "mapping_present_provider_ignored",
        },
        {
            "source_name": "민수", "corpus_mapping": None, "glossary_mapping": None,
            "character_memory_mapping": None, "selected_character_memory_entry": None,
            "rendered_prompt_mapping": None, "mapping_present_in_prompt": False,
            "mapping_omitted_by_budget": False, "raw_response_residual": "수",
            "expected_target_representation": None, "unresolved": True,
            "evidence_class": "missing_name_mapping_and_incomplete_name_normalization",
        },
    ]
    payloads = {
        "historical_execution_seal.json": {
            **common, "status": "PASS", "execution_status": "completed",
            "canary_status": "candidate_structural_failed", "provider_requests_consumed": 1,
            "candidate_provider_success": True, "candidate_timeout": False,
            "candidate_structural_pass": False,
            "prompt_contract_structural_verification_passed": False,
            "failure_reasons": ["hangul_residual", "bilingual_layout"],
            "not_provider_error": True, "not_timeout": True, "not_source_echo": True,
            "not_incomplete_output": True, "candidate_improved": None,
            "translation_quality_passed": None, "claim_hash_unchanged": True,
            "response_hash_unchanged": True,
        },
        "claim_lifecycle.json": {
            **common, "status": "PASS", "claim_status": "consumed",
            "authorized_request_budget": 1, "actual_requests_consumed": 1,
            "unused_budget": 0, "replay_allowed": False,
            "claim_deleted": False, "claim_recreated": False, "claim_overwritten": False,
            "claim_hash_unchanged": True,
        },
        "structural_failure_classification.json": {
            **common, "status": "PASS",
            "primary_failure_class": "target_language_name_resolution_failure",
            "structural_failure_class": "mixed_language_inline_output",
            "failure_subtype": "inline_hangul_name_residual",
            **trace,
            "bilingual_layout": True,
            "bilingual_layout_interpretation": "upper_level_mixed_language_classification",
        },
        "name_resolution_trace.json": {
            **common, "status": "PASS", "exact_source_character_names": ["영희", "민수"],
            "corpus_contains_name_mapping": False, "available_glossary_entries": [],
            "selected_character_memory_entries": selected_character_entries,
            "character_records_considered": metadata.get("character_records_considered"),
            "character_records_selected": metadata.get("character_records_selected"),
            "prompt_budget_exhausted": metadata.get("budget_exhausted"),
            "name_evidence": name_evidence,
            "validation_detected_but_did_not_repair": True,
        },
        "prompt_name_mapping_evidence.json": {
            **common, "status": "PASS", "prompt_fingerprint": plan["prompt_fingerprint"],
            "request_plan_fingerprint": plan["request_plan_fingerprint"],
            "glossary_rendered_as_none": "【Glossary】無" in prompt,
            "character_memory_rendered": "人物一致性記憶" in prompt,
            "yeonghui_mapping_present_in_prompt": "人物固定譯名：Yeong-hui" in prompt,
            "minsu_mapping_present_in_prompt": False,
            "prompt_budget_exhausted": metadata.get("budget_exhausted"),
            "raw_response_residual_names": ["영희", "수"],
            "name_evidence": name_evidence,
            "invented_name_mappings": [],
        },
        "remediation_decision.json": {
            **common, "status": "PASS", "remediation_class": "multiple_contributing_causes",
            "contributing_classes": [
                "mapping_present_provider_ignored",
                "missing_name_mapping",
                "incomplete_name_normalization",
            ],
            "yeonghui_decision": "mapping_present_provider_ignored",
            "minsu_decision": "missing_name_mapping_and_incomplete_name_normalization",
            "mapping_not_selected": False, "mapping_dropped_by_budget": False,
            "prompt_change_authorized": False, "glossary_change_authorized": False,
            "provider_rerun_authorized": False,
        },
        "sealing_summary.json": {
            **common, "status": "PASS", "offline_only": True,
            "execution_status": "completed", "canary_status": "candidate_structural_failed",
            "primary_failure_class": "target_language_name_resolution_failure",
            "structural_failure_class": "mixed_language_inline_output",
            "failure_subtype": "inline_hangul_name_residual",
            "remediation_class": "multiple_contributing_causes",
            "provider_requests_consumed": 1, "provider_requests_added": 0,
            "claim_hash_unchanged": True, "response_hash_unchanged": True,
            "failed": 0, "tracked_deletions": 0, "frozen_files_modified": 0,
        },
    }
    artifacts = {ARTIFACT_ROOT / name: canonical(payload) for name, payload in payloads.items()}
    if CLAIM.read_bytes() != claim_before:
        raise ValueError("stage1258-claim-mutated")
    if RESPONSE.read_bytes() != response_before:
        raise ValueError("stage1258-response-mutated")
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
    historical_names = [
        "preflight.json", "authorization_claim.json", "candidate_request.json",
        "candidate_response.json", "structural_validation.json",
        "final_activation_decision.json", "execution_summary.json",
    ]
    source_paths = ["tools/generate_te_v720_stage1258a_candidate_structural_failure_sealing.py"]
    test_paths = [
        "tests/unit/test_stage1258a_candidate_structural_failure_sealing.py",
        "ntpe_te_v720_stage1258a_candidate_structural_failure_sealing_test.py",
        "tests/integration/translation_engine_v720_stage1258a_candidate_structural_failure_sealing_test.py",
    ]
    manifest = {
        "schema_version": "te-v7.2-stage12.5.8-execution-seal-v1",
        "stage": STAGE,
        "preparation_manifest_sha256": sha(PREPARATION_MANIFEST.read_bytes()),
        "historical_execution_hashes": {
            name: sha((HISTORICAL_ROOT / name).read_bytes()) for name in historical_names
        },
        "root_cause_artifact_hashes": {
            path.relative_to(ROOT).as_posix(): sha(data) for path, data in artifacts.items()
        },
        "source_hashes": {path: sha((ROOT / path).read_bytes()) for path in source_paths},
        "test_hashes": {path: sha((ROOT / path).read_bytes()) for path in test_paths},
        "release_sha256": sha(RELEASE.read_bytes()),
        "provider_requests_added": 0, "network_requests_added": 0,
        "claim_hash_unchanged": True, "response_hash_unchanged": True,
        "tracked_deletions": 0, "frozen_files_modified": 0,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_bytes(canonical(manifest))
    return MANIFEST


def main() -> int:
    artifacts = write_artifacts()
    manifest = write_manifest(artifacts)
    print(json.dumps({
        "status": "PASS", "artifacts": len(artifacts),
        "manifest": manifest.relative_to(ROOT).as_posix(),
        "provider_requests_added": 0, "network_requests_added": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
