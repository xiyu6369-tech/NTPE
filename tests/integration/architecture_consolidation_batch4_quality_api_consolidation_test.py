from __future__ import annotations

import hashlib
from pathlib import Path
import socket

import pytest

from ntpe.corpus import manage
from ntpe.quality import assess, build_review_view
from core.translation_quality_corpus import load_golden_corpus
from core.translation_quality_defects import verify_defect_artifact
from core.translation_quality_metrics import verify_quality_metrics_artifact


ROOT = Path(__file__).resolve().parents[2]
DEFECTS = ROOT / "artifacts/te_v71_stage111/TE_V71_STAGE111_TRANSLATION_DEFECTS.json"
METRICS = ROOT / "artifacts/te_v71_stage112/TE_V71_STAGE112_QUALITY_METRICS.json"
REVIEW = ROOT / "artifacts/te_v71_stage113/TE_V71_STAGE113_REVIEW.json"
PLANS = ROOT / "artifacts/te_v71_stage114/TE_V71_STAGE114_PROMPT_IMPROVEMENT_PLAN.json"
DECISION = ROOT / "artifacts/te_v71_stage115/TE_V71_STAGE115_REVIEW_DECISION_CONTRACT.json"
CORPUS = ROOT / "quality_corpus/golden_review/te_v71_initial_defects.json"
GOVERNANCE = ROOT / "artifacts/te_v71_stage116/TE_V71_STAGE116_GOLDEN_CORPUS_GOVERNANCE.json"
FROZEN = (DEFECTS, METRICS, REVIEW, PLANS, DECISION, CORPUS, GOVERNANCE)


def _hashes() -> dict[str, str]:
    return {path.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in FROZEN}


def test_real_stage11_chain_has_new_legacy_parity_without_writes_or_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "create_connection", blocked)
    before = _hashes()
    defect_payload = verify_defect_artifact(DEFECTS)
    metric_payload = verify_quality_metrics_artifact(METRICS)
    legacy_corpus = load_golden_corpus(CORPUS)

    assessment = assess(defects=DEFECTS, metrics=METRICS)
    review = build_review_view(review_artifact=REVIEW, improvement_plans=PLANS, human_decision=DECISION)
    corpus = manage(corpus=CORPUS, governance_record=GOVERNANCE)

    assert len(assessment.defects) == defect_payload["defect_count"] == 6
    assert assessment.blocking_defect_count == defect_payload["blocking_defect_count"] == 1
    assert assessment.quality_pass == metric_payload["quality_pass"] is False
    assert assessment.overall_score == 41.91
    assert {plan.implementation_status for plan in review.improvement_plans} == {"planned_not_applied"}
    assert review.human_decision is not None and review.human_decision.decision.value == "accepted"
    assert not review.decision_applied and not review.corpus_approval_granted
    assert corpus.cases == legacy_corpus
    assert corpus.approved_case_count == corpus.approved_translation_count == 0
    assert _hashes() == before


def test_facade_calls_are_deterministic_and_do_not_touch_runtime_prompt_or_provider() -> None:
    runtime = ROOT / "core/translation_runtime"
    prompt = ROOT / "core/prompt_compiler"
    provider = ROOT / "core/ai_provider"
    boundaries = tuple(path for base in (runtime, prompt, provider) for path in base.rglob("*.py"))
    before = {path: hashlib.sha256(path.read_bytes()).digest() for path in boundaries}
    assert assess(defects=DEFECTS, metrics=METRICS) == assess(defects=DEFECTS, metrics=METRICS)
    assert build_review_view(review_artifact=REVIEW, improvement_plans=PLANS, human_decision=DECISION) == build_review_view(review_artifact=REVIEW, improvement_plans=PLANS, human_decision=DECISION)
    assert manage(corpus=CORPUS, governance_record=GOVERNANCE) == manage(corpus=CORPUS, governance_record=GOVERNANCE)
    assert {path: hashlib.sha256(path.read_bytes()).digest() for path in boundaries} == before


def test_single_public_import_and_legacy_imports_remain_available() -> None:
    import ntpe
    from core.translation_quality_framework_integration import build_quality_framework_integration

    assert callable(ntpe.quality.assess)
    assert callable(ntpe.quality.build_review_view)
    assert callable(ntpe.corpus.manage)
    assert callable(build_quality_framework_integration)

