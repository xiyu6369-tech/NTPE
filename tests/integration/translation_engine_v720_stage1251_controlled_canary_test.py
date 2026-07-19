from __future__ import annotations

import hashlib
import json
from pathlib import Path

from core.shared.evidence import canonical_json_bytes
from core.translation_quality_canary import ACTIVATION_GATE_READY, CHECKLIST


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts/te_v72_canary"
MANIFEST = ROOT / "manifests/te_v720_controlled_canary_manifest.json"
MILESTONE_A = ROOT / "manifests/te_v720_milestone_a_translation_quality_integration_manifest.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_required_artifact_tree_is_complete_and_canonical() -> None:
    required = (
        "baseline/run_summary.json", "candidate/run_summary.json",
        "comparison_report.json", "execution_summary.json",
        "quality_review_template.json", "performance_summary.json", "canary_evidence.json",
    )
    for relative in required:
        path = ARTIFACT_ROOT / relative
        payload = _json(path)
        assert path.read_bytes() == canonical_json_bytes(payload), relative


def test_baseline_candidate_parameters_match_and_only_flags_differ() -> None:
    baseline = _json(ARTIFACT_ROOT / "baseline/run_summary.json")
    candidate = _json(ARTIFACT_ROOT / "candidate/run_summary.json")
    assert baseline["configuration"] == candidate["configuration"]
    assert len(baseline["runs"]) == len(candidate["runs"]) == 6
    for left, right in zip(baseline["runs"], candidate["runs"], strict=True):
        assert left["source_sha256"] == right["source_sha256"]
        assert left["input_fingerprint"] == right["input_fingerprint"]
        assert left["configuration_fingerprint"] == right["configuration_fingerprint"]
        assert left["flags"] != right["flags"]
        assert left["provider_requests"] == right["provider_requests"] == 0
        assert left["network_requests"] == right["network_requests"] == 0


def test_quality_comparison_is_explicitly_not_reviewable_and_gate_stays_ready() -> None:
    comparison = _json(ARTIFACT_ROOT / "comparison_report.json")
    evidence = _json(ARTIFACT_ROOT / "canary_evidence.json")
    assert comparison["canary_pass"] is False
    assert comparison["status"] == "FAIL_CLOSED_INSUFFICIENT_QUALITY_EVIDENCE"
    assert comparison["reviewed_checklist_rows"] == 0
    assert comparison["expected_checklist_rows"] == 6 * len(CHECKLIST)
    assert evidence["activation_gate"] == ACTIVATION_GATE_READY
    assert evidence["production_authorized"] is False


def test_review_template_has_all_required_fields_and_dimensions() -> None:
    template = _json(ARTIFACT_ROOT / "quality_review_template.json")
    assert len(template["chunks"]) == 6
    for chunk in template["chunks"]:
        assert {"overall_score", "strength", "weakness", "regression", "notes"} <= set(chunk)
        assert set(chunk["checklist"]) == set(CHECKLIST)
        assert all(value is None for value in chunk["checklist"].values())


def test_metrics_include_selection_budget_tokens_and_latency_without_prompt_payload() -> None:
    performance = _json(ARTIFACT_ROOT / "performance_summary.json")
    assert performance["character_selected"] >= 6
    assert performance["context_selected"] >= 6
    assert performance["scene_selected"] >= 6
    assert performance["candidate_budget_usage_tokens"] > 0
    assert performance["candidate_prompt_tokens"] > performance["baseline_prompt_tokens"]
    assert performance["baseline_integration_latency"] >= 0
    assert performance["candidate_integration_latency"] >= 0
    serialized = "\n".join(path.read_text(encoding="utf-8") for path in ARTIFACT_ROOT.rglob("*.json")).lower()
    for forbidden in ("full_prompt", "provider_payload", "response_body", "api_key", "authorization_token"):
        assert forbidden not in serialized


def test_manifest_is_canonical_and_all_hashes_match() -> None:
    payload = _json(MANIFEST)
    assert MANIFEST.read_bytes() == canonical_json_bytes(payload)
    for section in ("source_hashes", "test_hashes", "evidence_hashes"):
        for relative, expected in payload[section].items():
            assert _sha(ROOT / relative) == expected, relative
    release = ROOT / "docs/releases/te_v7_2/TE_V720_CONTROLLED_CANARY.md"
    assert _sha(release) == payload["release_hash"]
    assert _sha(MILESTONE_A) == payload["milestone_a_manifest_sha256"]


def test_manifest_boundaries_remain_nonproduction_and_provider_free() -> None:
    payload = _json(MANIFEST)
    assert payload["activation_gate"] == ACTIVATION_GATE_READY
    assert payload["provider_requests"] == payload["network_requests"] == 0
    assert payload["runtime_modified"] is False
    assert payload["prompt_modified"] is False
    assert payload["production_authorized"] is False
    assert payload["commit_performed"] is False
    assert payload["push_performed"] is False
    assert payload["tag_performed"] is False


def test_canary_source_has_no_provider_network_runtime_or_output_execution_path() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "core/translation_quality_canary").glob("*.py")
    ).lower()
    assert "requests." not in source
    assert "httpx" not in source
    assert "urllib.request" not in source
    assert "providermanager" not in source
    assert "launcher_translate" not in source
    assert "write_output" not in source
