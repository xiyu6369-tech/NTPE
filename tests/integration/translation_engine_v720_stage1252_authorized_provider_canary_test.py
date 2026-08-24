from __future__ import annotations

import hashlib
import json
from pathlib import Path

from core.shared.evidence import canonical_json_bytes
from core.translation_quality_canary import ACTIVATION_GATE_READY, CHECKLIST

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/te_v72_canary"
ARTIFACT = FIXTURES
MANIFEST = ROOT / "manifests/te_v720_authorized_provider_canary_manifest.json"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_execution_is_bounded_and_nonproduction() -> None:
    summary = _json(ARTIFACT / "execution_summary.json")
    metrics = _json(ARTIFACT / "provider_metrics.json")
    assert summary["provider_requests"] == summary["network_requests"] == 4
    assert metrics["attempt_limit_per_arm"] == 1
    assert metrics["retry"] == 0 and metrics["fallback"] is False and metrics["parallel_jobs"] == 1
    assert all(value is False for value in summary["boundary"].values())


def test_outputs_and_manual_review_template_exist() -> None:
    assert len(list((ARTIFACT / "baseline_output").glob("*.txt"))) == 2
    assert len(list((ARTIFACT / "candidate_output").glob("*.txt"))) == 2
    review = (ARTIFACT / "manual_review.md").read_text(encoding="utf-8")
    for field in ("Overall:", "Major improvement:", "Minor improvement:", "Regression:", "Comments:"):
        assert review.count(field) == 2


def test_quality_is_not_auto_approved() -> None:
    report = _json(ARTIFACT / "quality_report.json")
    assert report["canary_pass"] is False
    assert report["human_review_completed"] is True
    assert report["decision"] == "candidate_regression_and_incomplete_pair"
    assert report["activation_gate"] == ACTIVATION_GATE_READY
    assert len(report["quality_cases"]) == 2
    reviewed, incomplete = report["quality_cases"]
    assert set(reviewed["checklist"]) == set(incomplete["checklist"]) == set(CHECKLIST)
    assert reviewed["overall"] == "Candidate regression"
    assert reviewed["review_status"] == "completed_candidate_regression"
    assert set(reviewed["checklist"].values()) <= {"Improved", "Same", "Regressed"}
    assert sum(value == "Regressed" for value in reviewed["checklist"].values()) == 3
    assert incomplete["overall"] == "Incomplete pair"
    assert incomplete["review_status"] == "incomplete_pair"
    assert all(value is None for value in incomplete["checklist"].values())


def test_evidence_and_manifest_are_canonical_and_hash_bound() -> None:
    evidence = ARTIFACT / "canary_execution_evidence.json"
    for path in (evidence, MANIFEST):
        assert path.read_bytes() == canonical_json_bytes(_json(path))
    manifest = _json(MANIFEST)
    assert manifest["evidence_sha256"] == hashlib.sha256(evidence.read_bytes()).hexdigest()
    assert manifest["estimated_prompt_tokens"] > 0
    assert manifest["estimated_completion_tokens"] >= 0
    assert manifest["latency_ms"] >= 0
    assert manifest["cost_status"] == "provider_did_not_supply_cost"
    assert manifest["activation_gate"] == ACTIVATION_GATE_READY
    assert manifest["human_review_completed"] is True and manifest["canary_pass"] is False
    assert manifest["decision"] == "candidate_regression_and_incomplete_pair"


def test_frozen_stage1251_manifest_is_not_in_new_evidence_inventory() -> None:
    manifest = _json(MANIFEST)
    assert "manifests/te_v720_controlled_canary_manifest.json" not in manifest["evidence_hashes"]
