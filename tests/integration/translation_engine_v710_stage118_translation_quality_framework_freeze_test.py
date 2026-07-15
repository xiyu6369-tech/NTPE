from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import pytest

from core.translation_quality_corpus import load_golden_corpus
from core.translation_quality_framework_integration import build_quality_framework_integration

ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT / "artifacts/te_v71_stage118/TE_V71_STAGE118_TRANSLATION_QUALITY_FRAMEWORK_FREEZE.json"
MANIFEST = ROOT / "manifests/te_v710_stage118_translation_quality_framework_freeze_manifest.json"
CORPUS = ROOT / "quality_corpus/golden_review/te_v71_initial_defects.json"


def _freeze():
    return json.loads(FREEZE.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _integration():
    return build_quality_framework_integration(
        root=ROOT, source_case_id="TQ-DEF-B", created_at="2026-07-15T02:00:00+08:00",
        defects_reference="artifacts/te_v71_stage111/TE_V71_STAGE111_TRANSLATION_DEFECTS.json",
        metrics_reference="artifacts/te_v71_stage112/TE_V71_STAGE112_QUALITY_METRICS.json",
        review_artifact_reference="artifacts/te_v71_stage113/TE_V71_STAGE113_REVIEW.json",
        improvement_plan_reference="artifacts/te_v71_stage114/TE_V71_STAGE114_PROMPT_IMPROVEMENT_PLAN.json",
        human_decision_reference="artifacts/te_v71_stage115/TE_V71_STAGE115_REVIEW_DECISION_CONTRACT.json",
        corpus_governance_reference="artifacts/te_v71_stage116/TE_V71_STAGE116_GOLDEN_CORPUS_GOVERNANCE.json",
        golden_corpus_reference="quality_corpus/golden_review/te_v71_initial_defects.json",
    )


@pytest.mark.parametrize("module", [
    "core.translation_quality_defects", "core.translation_quality_metrics",
    "core.translation_quality_review_artifacts", "core.translation_prompt_improvement_planner",
    "core.translation_quality_review_decision", "core.translation_quality_corpus",
    "core.translation_quality_corpus_governance", "core.translation_quality_framework_integration",
])
def test_all_framework_modules_import(module: str) -> None:
    assert importlib.import_module(module)


def test_freeze_identity_and_status() -> None:
    payload = _freeze()
    assert payload["stage"] == "TE-v7.1-Stage11.8" and payload["version"] == "7.1.0-stage11.8"
    assert payload["status"] == "completed" and payload["freeze"] is True


@pytest.mark.parametrize("key", ["artifacts", "manifests", "root_tests", "integration_tests"])
def test_every_frozen_inventory_path_exists(key: str) -> None:
    assert all((ROOT / path).is_file() for path in _freeze()[key])


def test_all_prior_stage_manifest_hashes_are_frozen() -> None:
    payload = _freeze()
    for index, path in enumerate(payload["manifests"], start=111):
        assert payload["integrity"][f"stage{index}_manifest_sha256"] == _sha(ROOT / path)


def test_every_file_in_prior_manifests_matches_sha256() -> None:
    for manifest_path in _freeze()["manifests"]:
        manifest = json.loads((ROOT / manifest_path).read_text(encoding="utf-8"))
        for path, expected in manifest["files"].items():
            assert _sha(ROOT / path) == expected, path


def test_stage117_integration_artifact_is_frozen() -> None:
    path = ROOT / "artifacts/te_v71_stage117/TE_V71_STAGE117_QUALITY_FRAMEWORK_INTEGRATION.json"
    assert _freeze()["integrity"]["stage117_integration_artifact_sha256"] == _sha(path)
    assert _integration().integration_status == "blocked" and _integration().integrity_status == "valid"


def test_golden_corpus_hash_and_content_are_frozen() -> None:
    assert _freeze()["integrity"]["golden_corpus_sha256"] == _sha(CORPUS)
    cases = load_golden_corpus(CORPUS)
    assert len(cases) == 6 and all(case.approved_final_translation is None for case in cases)


def test_no_plan_was_applied() -> None:
    plan = json.loads((ROOT / "artifacts/te_v71_stage114/TE_V71_STAGE114_PROMPT_IMPROVEMENT_PLAN.json").read_text(encoding="utf-8"))
    assert plan["plans_applied"] == 0 and all(row["implementation_status"] == "planned_not_applied" for row in plan["plans"])


def test_no_decision_was_applied() -> None:
    decision = json.loads((ROOT / "artifacts/te_v71_stage115/TE_V71_STAGE115_REVIEW_DECISION_CONTRACT.json").read_text(encoding="utf-8"))
    assert decision["fixture"]["not_applied"] and decision["boundary"]["decision_applied"] is False


def test_no_corpus_approval_was_created() -> None:
    governance = json.loads((ROOT / "artifacts/te_v71_stage116/TE_V71_STAGE116_GOLDEN_CORPUS_GOVERNANCE.json").read_text(encoding="utf-8"))
    assert governance["current_corpus_summary"]["approved_cases"] == 0
    assert governance["current_corpus_summary"]["approved_translations"] == 0


def test_framework_boundary_is_frozen_and_inactive() -> None:
    boundary = _freeze()["boundary"]
    zero = {"network_requests", "plans_applied", "decisions_applied", "approved_cases_created", "approved_translations_added"}
    assert all(boundary[key] == 0 for key in zero)
    assert boundary["framework_frozen"] is True and boundary["te_v72_started"] is False
    assert all(value is False for key, value in boundary.items() if key not in zero | {"framework_frozen"})


def test_freeze_does_not_claim_quality_improvement() -> None:
    boundary = _freeze()["boundary"]
    assert boundary["translation_quality_improved"] is False
    assert boundary["new_translation_generated"] is False


def test_freeze_adds_no_new_core_module() -> None:
    assert not (ROOT / "core/translation_quality_framework_freeze").exists()


def test_release_document_declares_future_compatibility_boundary() -> None:
    text = (ROOT / "docs/releases/te_v7_1/TE_V710_STAGE118_TRANSLATION_QUALITY_FRAMEWORK_FREEZE.md").read_text(encoding="utf-8")
    assert "Future TE v7.2 work" in text and "does not start TE v7.2" in text


def test_freeze_manifest_is_deterministic_and_complete() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["stage"] == "TE-v7.1-Stage11.8" and manifest["status"] == "frozen"
    assert manifest["freeze"] is True and len(manifest["frozen_stage_manifests"]) == 7


def test_freeze_manifest_anchors_prior_manifests() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for path, expected in manifest["frozen_stage_manifests"].items():
        assert _sha(ROOT / path) == expected


def test_freeze_manifest_files_match() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for path, expected in manifest["files"].items():
        assert _sha(ROOT / path) == expected


def test_validation_summary_is_fully_stable() -> None:
    summary = _freeze()["validation_summary"]
    assert all(summary.values()) and summary["framework_frozen"] is True


def test_root_and_integration_test_inventory_covers_all_stages() -> None:
    payload = _freeze()
    assert len(payload["root_tests"]) == 8 and len(payload["integration_tests"]) == 8


def test_required_historical_regressions_are_frozen() -> None:
    assert len(_freeze()["regressions"]) == 7
    assert "TE-v6.0-Final-Freeze" in _freeze()["regressions"]
