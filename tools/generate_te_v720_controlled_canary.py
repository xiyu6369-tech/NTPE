from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.shared.evidence import canonical_json_bytes, write_canonical_json
from core.translation_quality_canary import (
    ACTIVATION_GATE_PASSED,
    ACTIVATION_GATE_READY,
    CHECKLIST,
    CanaryConfiguration,
    build_comparison_report,
    run_offline_canary_case,
)


CORPUS = ROOT / "tests/fixtures/te_v72_canary/golden_corpus.json"
ARTIFACT_ROOT = ROOT / "artifacts/te_v72_canary"
MANIFEST = ROOT / "manifests/te_v720_controlled_canary_manifest.json"
MILESTONE_A_MANIFEST = ROOT / "manifests/te_v720_milestone_a_translation_quality_integration_manifest.json"

SOURCE_FILES = (
    "core/translation_quality_canary/__init__.py",
    "core/translation_quality_canary/comparison.py",
    "core/translation_quality_canary/fixtures.py",
    "core/translation_quality_canary/models.py",
    "core/translation_quality_canary/runner.py",
    "tools/generate_te_v720_controlled_canary.py",
    "tests/fixtures/te_v72_canary/golden_corpus.json",
    "docs/releases/te_v7_2/TE_V720_CONTROLLED_CANARY.md",
)
TEST_FILES = (
    "tests/unit/test_translation_quality_canary.py",
    "tests/integration/translation_engine_v720_stage1251_controlled_canary_test.py",
    "ntpe_te_v720_stage1251_controlled_canary_test.py",
)


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _fingerprint(value: object) -> str:
    return _sha_bytes(canonical_json_bytes(value))


def _hashes(paths: tuple[str, ...]) -> dict[str, str]:
    return {path: _sha_file(ROOT / path) for path in paths}


def _write(relative: str, payload: object) -> Path:
    path = ARTIFACT_ROOT / relative
    write_canonical_json(path, payload)
    return path


def main() -> int:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    corpus_sha = _sha_file(CORPUS)
    glossary_sha = _fingerprint({"영희": "Yeong-hui", "민수": "Min-su"})
    configuration = CanaryConfiguration(
        model="meta/llama-3.3-70b-instruct",
        timeout_seconds=180,
        glossary_sha256=glossary_sha,
        profile="literary-ko-zh-TW",
        corpus_sha256=corpus_sha,
    )
    pairs = [
        run_offline_canary_case(
            case_id=item["case_id"],
            categories=tuple(item["categories"]),
            source_text=item["source_text"],
            configuration=configuration,
        )
        for item in corpus["cases"]
    ]
    comparison = build_comparison_report(
        pairs,
        corpus_human_reviewed=bool(corpus["human_reviewed_translation_pairs"]),
    )
    semantic_identity = {
        "stage": "TE-v7.2-Stage12.5.1",
        "configuration": configuration.to_dict(),
        "corpus_sha256": corpus_sha,
        "case_ids": [pair.case_id for pair in pairs],
        "input_fingerprints": [pair.baseline.input_fingerprint for pair in pairs],
        "candidate_selection_fingerprints": [pair.candidate.prompt_sha256 for pair in pairs],
        "comparison_status": comparison["status"],
        "provider_requests_added": 0,
        "network_requests_added": 0,
    }
    deterministic_fingerprint = _fingerprint(semantic_identity)
    baseline = {
        "arm": "baseline",
        "quality_integration": False,
        "character": False,
        "context": False,
        "naturalness": False,
        "configuration": configuration.to_dict(),
        "runs": [pair.baseline.to_dict() for pair in pairs],
    }
    candidate = {
        "arm": "candidate",
        "quality_integration": True,
        "character": True,
        "context": True,
        "naturalness": True,
        "configuration": configuration.to_dict(),
        "runs": [pair.candidate.to_dict() for pair in pairs],
    }
    execution = {
        "stage": "TE-v7.2-Stage12.5.1",
        "mode": "offline_prompt_preparation_only",
        "chunk_count": len(pairs),
        "same_model": True,
        "same_chunk": True,
        "same_timeout": True,
        "same_glossary": True,
        "same_profile": True,
        "same_corpus": True,
        "all_pair_parameters_verified": all(pair.parity_verified for pair in pairs),
        "only_feature_flags_differ": all(pair.only_feature_flags_differ for pair in pairs),
        "translation_pairs_complete": False,
        "provider_requests_added": 0,
        "network_requests_added": 0,
        "runtime_behavior_unchanged": True,
        "disabled_path_unchanged": True,
        "prompt_builder_modified": False,
        "provider_modified": False,
        "resume_modified": False,
        "output_modified": False,
    }
    review_template = {
        "schema_version": "te-v7.2-stage12.5.1-quality-review-template-v1",
        "allowed_comparison_values": ["Improved", "Same", "Regressed"],
        "chunks": [
            {
                "case_id": pair.case_id,
                "overall_score": None,
                "strength": None,
                "weakness": None,
                "regression": None,
                "notes": None,
                "checklist": {dimension: None for dimension in CHECKLIST},
            }
            for pair in pairs
        ],
    }
    baseline_latency = sum(pair.baseline.integration_latency_microseconds for pair in pairs)
    candidate_latency = sum(pair.candidate.integration_latency_microseconds for pair in pairs)
    performance = {
        "chunk_count": len(pairs),
        "latency_unit": "microseconds",
        "baseline_integration_latency": baseline_latency,
        "candidate_integration_latency": candidate_latency,
        "integration_latency_delta": candidate_latency - baseline_latency,
        "baseline_prompt_tokens": sum(pair.baseline.prompt_tokens for pair in pairs),
        "candidate_prompt_tokens": sum(pair.candidate.prompt_tokens for pair in pairs),
        "candidate_budget_usage_tokens": sum(pair.candidate.budget_usage_tokens for pair in pairs),
        "character_selected": sum(pair.candidate.character_selected for pair in pairs),
        "context_selected": sum(pair.candidate.context_selected for pair in pairs),
        "scene_selected": sum(pair.candidate.scene_selected for pair in pairs),
    }
    gate = ACTIVATION_GATE_PASSED if comparison["canary_pass"] else ACTIVATION_GATE_READY
    evidence = {
        "stage": "TE-v7.2-Stage12.5.1",
        "verification_stage": True,
        "canary_status": comparison["status"],
        "canary_pass": comparison["canary_pass"],
        "activation_gate": gate,
        "failure_reason": None if comparison["canary_pass"] else "no complete human-reviewed baseline/candidate translation pairs",
        "corpus_case_count": len(pairs),
        "quality_checklist_statistics": comparison["statistics"],
        "quality_rows_reviewed": comparison["reviewed_checklist_rows"],
        "quality_rows_expected": comparison["expected_checklist_rows"],
        "provider_requests_added": 0,
        "network_requests_added": 0,
        "runtime_modified": False,
        "prompt_builder_modified": False,
        "provider_modified": False,
        "resume_modified": False,
        "output_modified": False,
        "production_authorized": False,
        "deterministic_fingerprint": deterministic_fingerprint,
    }

    artifact_paths = [
        _write("baseline/run_summary.json", baseline),
        _write("candidate/run_summary.json", candidate),
        _write("comparison_report.json", comparison),
        _write("execution_summary.json", execution),
        _write("quality_review_template.json", review_template),
        _write("performance_summary.json", performance),
        _write("canary_evidence.json", evidence),
    ]
    release_path = ROOT / "docs/releases/te_v7_2/TE_V720_CONTROLLED_CANARY.md"
    manifest = {
        "stage": "TE-v7.2-Stage12.5.1",
        "schema_version": "1.0",
        "activation_gate": gate,
        "canary_pass": comparison["canary_pass"],
        "source_hashes": _hashes(SOURCE_FILES),
        "test_hashes": _hashes(TEST_FILES),
        "evidence_hashes": {
            path.relative_to(ROOT).as_posix(): _sha_file(path) for path in artifact_paths
        },
        "release_hash": _sha_file(release_path),
        "milestone_a_manifest": MILESTONE_A_MANIFEST.relative_to(ROOT).as_posix(),
        "milestone_a_manifest_sha256": _sha_file(MILESTONE_A_MANIFEST),
        "deterministic_fingerprint": deterministic_fingerprint,
        "provider_requests": 0,
        "network_requests": 0,
        "runtime_modified": False,
        "prompt_modified": False,
        "production_authorized": False,
        "commit_performed": False,
        "push_performed": False,
        "tag_performed": False,
    }
    write_canonical_json(MANIFEST, manifest)
    print(json.dumps({
        "status": comparison["status"],
        "activation_gate": gate,
        "deterministic_fingerprint": deterministic_fingerprint,
        "manifest": MANIFEST.relative_to(ROOT).as_posix(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
