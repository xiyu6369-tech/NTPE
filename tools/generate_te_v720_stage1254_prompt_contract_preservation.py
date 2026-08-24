from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.literary import estimate_tokens
from core.shared.evidence import canonical_json_bytes
from core.translation_quality_integration_v72.prompt_contract import (
    REFERENCE_END,
    REFERENCE_START,
    scan_dynamic_section,
    verify_candidate_prompt,
)
from core.translation_quality_provider_canary.framework import _build_prompts
from core.production_runtime.manifest import (
    get_te_v7_stage_path,
    get_te_v7_artifact_path,
)


ARTIFACT_ROOT = ROOT / "artifacts/te_v72_prompt_contract_preservation"
MANIFEST = ROOT / "manifests/te_v720_stage1254_prompt_contract_preservation_manifest.json"
RELEASE = ROOT / "docs/releases/te_v7_2/TE_V720_STAGE1254_PROMPT_CONTRACT_PRESERVATION.md"
CORPUS = ROOT / "tests/fixtures/te_v72_canary/golden_corpus.json"
CLAIM = get_te_v7_artifact_path(ROOT, "te_v72_canary_execution", "execution_claim.json")
STAGE1252_MANIFEST = ROOT / "manifests/te_v720_authorized_provider_canary_manifest.json"
MANAGED_ARTIFACTS = (
    "baseline_prompt_snapshot.txt",
    "candidate_prompt_before_snapshot.txt",
    "candidate_prompt_after_snapshot.txt",
    "dynamic_section_scan_report.json",
    "prompt_contract_preservation_evidence.json",
    "prompt_ordering_diff.json",
    "serialization_invariants.json",
    "token_dilution_metrics.json",
)
SOURCE_FILES = (
    "core/translation_quality_integration_v72/__init__.py",
    "core/translation_quality_integration_v72/adapter.py",
    "core/translation_quality_integration_v72/prompt_contract.py",
    "tools/generate_te_v720_stage1254_prompt_contract_preservation.py",
    "tests/unit/test_translation_quality_prompt_contract_v72.py",
    "tests/integration/translation_engine_v720_stage1254_prompt_contract_preservation_test.py",
    "ntpe_te_v720_stage1254_prompt_contract_preservation_test.py",
)


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def _reference_section(candidate: str) -> str:
    container = candidate[candidate.index(REFERENCE_START):candidate.index(REFERENCE_END) + len(REFERENCE_END)]
    body = container.split("\n", 6)[6]
    return body[: -(len(REFERENCE_END) + 1)]


def build_outputs() -> tuple[dict[str, bytes], dict[str, object]]:
    case = json.loads(CORPUS.read_text(encoding="utf-8"))["cases"][0]
    source = str(case["source_text"])
    system, baseline, after, metadata = _build_prompts(str(case["case_id"]), source)
    section = _reference_section(after)
    insertion = baseline.rfind(source)
    before = baseline[:insertion] + section + "\n" + baseline[insertion:]
    invariants = verify_candidate_prompt(after, source).to_dict()
    baseline_tokens = estimate_tokens(system) + estimate_tokens(baseline)
    before_tokens = estimate_tokens(system) + estimate_tokens(before)
    after_tokens = estimate_tokens(system) + estimate_tokens(after)
    policy_tokens = estimate_tokens(baseline[:baseline.index("\n【Profile】")])
    source_tokens = estimate_tokens(source)
    metrics = {
        "absolute_added_tokens": after_tokens - baseline_tokens,
        "baseline_estimated_prompt_tokens": baseline_tokens,
        "budget_rejection": False,
        "budget_truncation": bool(metadata["budget_exhausted"]),
        "candidate_after_fix_estimated_prompt_tokens": after_tokens,
        "candidate_before_fix_estimated_prompt_tokens": before_tokens,
        "character_allocation_tokens": metadata["character_tokens"],
        "context_allocation_tokens": metadata["context_tokens"],
        "naturalness_allocation_tokens": metadata["naturalness_tokens"],
        "relative_growth_percentage": round((after_tokens - baseline_tokens) * 100 / baseline_tokens, 2),
        "scene_allocation_tokens": metadata["scene_tokens"],
        "source_token_share_percentage": round(source_tokens * 100 / after_tokens, 2),
        "source_tokens": source_tokens,
        "translation_contract_token_share_percentage": round(policy_tokens * 100 / after_tokens, 2),
        "translation_contract_tokens": policy_tokens,
    }
    claim = json.loads(CLAIM.read_text(encoding="utf-8"))
    historical = json.loads(STAGE1252_MANIFEST.read_text(encoding="utf-8"))
    scan = {
        "forbidden_tokens": ["【Korean】", "【Output】", "譯文：", "Source:", "Translation:", "exact-source"],
        "reference_section_violations": list(scan_dynamic_section(section, source)),
        "scan_clean": not scan_dynamic_section(section, source),
    }
    ordering = {
        "candidate_reference_before_source": after.index(REFERENCE_START) < after.index(f"【Korean】\n{source}"),
        "reference_container_closed_before_korean_marker": after.index(REFERENCE_END) < after.index(f"【Korean】\n{source}"),
        "source_boundary_contiguous": f"【Korean】\n{source}\n【Output】" in after,
    }
    preliminary = {
        "baseline_prompt_snapshot.txt": baseline.encode("utf-8"),
        "candidate_prompt_before_snapshot.txt": before.encode("utf-8"),
        "candidate_prompt_after_snapshot.txt": after.encode("utf-8"),
        "dynamic_section_scan_report.json": canonical_json_bytes(scan),
        "prompt_ordering_diff.json": canonical_json_bytes(ordering),
        "serialization_invariants.json": canonical_json_bytes(invariants),
        "token_dilution_metrics.json": canonical_json_bytes(metrics),
    }
    evidence = {
        "activation_gate": "translation_quality_integration_ready_for_controlled_canary",
        "active_production_authorized": False,
        "artifact_hashes": {name: _sha_bytes(value) for name, value in sorted(preliminary.items())},
        "automatic_rollout_authorized": False,
        "execution_claim_replayed": False,
        "fallback": False,
        "formal_output_replacement_authorized": False,
        "historical_provider_requests": historical["provider_requests"],
        "network_requests_added": 0,
        "offline_status": "prompt_contract_preservation_offline_validated",
        "production_authorized": False,
        "provider_requests_added": 0,
        "quality_improvement_proven": False,
        "retry_added": 0,
        "stage": "TE-v7.2-Stage12.5.4A",
        "stage1252_claim_consumed": bool(claim["claimed"]),
        "status": "offline_validated",
        "structure_validation_passed": bool(invariants["valid"]),
        "token_growth_known_canary_risk": True,
        "token_metrics": metrics,
    }
    preliminary["prompt_contract_preservation_evidence.json"] = canonical_json_bytes(evidence)
    manifest = {
        "activation_gate": evidence["activation_gate"],
        "active_production_authorized": False,
        "artifact_hashes": {f"artifacts/te_v72_prompt_contract_preservation/{name}": _sha_bytes(value) for name, value in sorted(preliminary.items())},
        "automatic_rollout_authorized": False,
        "commit_performed": False,
        "execution_claim_replayed": False,
        "fallback": False,
        "formal_output_replacement_authorized": False,
        "network_requests_added": 0,
        "offline_status": evidence["offline_status"],
        "production_authorized": False,
        "provider_requests_added": 0,
        "push_performed": False,
        "release_sha256": _sha(RELEASE),
        "retry_added": 0,
        "schema_version": "te-v7.2-stage12.5.4a-acceptance-completion-v1",
        "source_hashes": {path: _sha(ROOT / path) for path in SOURCE_FILES},
        "stage": "TE-v7.2-Stage12.5.4A",
        "tag_performed": False,
    }
    return preliminary, manifest


def main() -> int:
    if not RELEASE.is_file():
        raise FileNotFoundError(RELEASE)
    artifacts, manifest = build_outputs()
    for name in MANAGED_ARTIFACTS:
        _write_bytes(ARTIFACT_ROOT / name, artifacts[name])
    _write_bytes(MANIFEST, canonical_json_bytes(manifest))
    print(json.dumps({"artifact_count": len(artifacts), "manifest": MANIFEST.relative_to(ROOT).as_posix(), "status": "offline_validated"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
