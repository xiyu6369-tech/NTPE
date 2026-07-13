from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from core.adaptive_context_production_rollout import (
    OUTCOME_VERSION,
    ProductionEvidence,
    ProductionOutcome,
    RollbackController,
    RolloutConfig,
    RolloutMetrics,
    collect_production_outcome,
    apply_production_rollout,
    evaluate_automatic_rollback,
    prior_rollback_reasons,
    rollback_quality_inputs,
    snapshot_resume_chunks,
)
from core.translation_release import build_te_v6_release_contract

ROOT = Path(__file__).resolve().parents[2]
SECRET = "原文與譯文不得進入 outcome 或 metrics"


def _qa(score: int, *, status: str = "accepted", issues: tuple[str, ...] = ()) -> dict[str, object]:
    return {
        "status": status,
        "passed": status == "accepted",
        "retry_required": status == "retry_required",
        "score": score,
        "issues": [{"code": code, "message": SECRET} for code in issues],
        "unified_quality_report": {
            "score": score,
            "decision": status,
            "accepted": status == "accepted",
            "retry_required": status == "retry_required",
            "merged_issues": [{"code": code} for code in issues],
        },
    }


def _state(path: Path, source_hash: str, qa: dict[str, object] | None, *, status: str = "success") -> None:
    row: dict[str, object] = {"status": status, "source_hash": source_hash}
    if qa is not None:
        row["qa"] = qa
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"chunks": {"000001": row}}, ensure_ascii=False), encoding="utf-8")


def _collect(
    sandbox: Path,
    *,
    current_score: int = 90,
    baseline_score: int = 90,
    current_status: str = "accepted",
    issues: tuple[str, ...] = (),
    activated: bool = True,
    resume: bool = False,
    provider_status: str = "success",
) -> tuple[ProductionOutcome, RolloutMetrics]:
    source_hash = "source-hash-1"
    current_dir = sandbox / "current" / "Golden_Set"
    baseline_dir = sandbox / "tests" / "literary" / "outputs" / "baseline" / "Golden_Set"
    row_status = "qa_failed" if current_status == "failed" else "success"
    current_qa = None if provider_status in {"timeout", "503"} else _qa(current_score, status=current_status, issues=issues)
    _state(current_dir / "original_ko_resume_state.json", source_hash, current_qa, status="failed" if current_qa is None else row_status)
    _state(baseline_dir / "original_ko_resume_state.json", source_hash, _qa(baseline_score))
    metrics = RolloutMetrics()
    digest = __import__("hashlib").sha256(source_hash.encode("utf-8")).hexdigest()
    metrics.records.append({
        "source_hash_sha256": digest,
        "chunk_index": 1,
        "decision": "activated" if activated else "not-sampled",
        "activated": activated,
        "payload_changed": activated,
        "blockers": [],
    })
    snapshot = frozenset({(digest, 1)}) if resume else frozenset()
    outcome = collect_production_outcome(
        {"records": [{"name": "Golden_Set", "output_dir": str(current_dir)}]},
        metrics,
        root=sandbox,
        baseline_stage="baseline",
        resume_snapshot=snapshot,
        provider_status=provider_status,
    )
    return outcome, metrics


def _decision(outcome: ProductionOutcome, *, provider_status: str = "success"):
    values = rollback_quality_inputs(outcome)
    return evaluate_automatic_rollback(
        new_issues=values.new_issues,
        quality_score=values.quality_score,
        baseline_quality_score=values.baseline_quality_score,
        qa_failure_rate=values.qa_failure_rate,
        baseline_qa_failure_rate=values.baseline_qa_failure_rate,
        provider_calls_added=0,
        anchor_mismatch=values.anchor_mismatch,
        replacement_count=values.replacement_count or 1,
        quality_evidence_complete=outcome.evidence_complete,
        provider_status=provider_status,
    )


def test_activated_acceptance_and_functional_regressions() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage0841_quality" / uuid.uuid4().hex
    try:
        accepted, _ = _collect(sandbox)
        assert accepted.evidence_complete and accepted.qa_accepted == 1
        assert not _decision(accepted).rollback
        for issues, reason in (
            (("PARAGRAPH_OMISSION_SUSPECTED",), "new-omission-issue"),
            (("UNSUPPORTED_DETAIL_HIGH_CONFIDENCE",), "new-unsupported-detail-issue"),
        ):
            outcome, _ = _collect(sandbox, issues=issues)
            decision = _decision(outcome)
            assert decision.rollback and decision.mode == "disabled" and reason in decision.reasons
        score, _ = _collect(sandbox, current_score=79, baseline_score=80)
        assert "quality-score-regression" in _decision(score).reasons
        qa_failed, _ = _collect(sandbox, current_status="failed")
        assert "qa-failure-rate-regression" in _decision(qa_failed).reasons
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_unsampled_and_resume_chunks_are_not_ace_quality_evidence() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage0841_scope" / uuid.uuid4().hex
    try:
        unsampled, _ = _collect(sandbox, activated=False, current_status="failed", issues=("OMISSION",))
        assert unsampled.activated_chunks == 0 and not unsampled.new_issue_codes
        resumed, _ = _collect(sandbox, resume=True, current_status="failed", issues=("OMISSION",))
        assert resumed.activated_chunks == 0 and resumed.resume_chunks == 1 and not resumed.new_issue_codes
        snap = snapshot_resume_chunks(sandbox / "current")
        assert len(snap) == 0  # failed/qa-failed state is never reusable resume evidence
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_provider_limitation_is_separate_but_quality_evidence_fails_closed() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage0841_provider" / uuid.uuid4().hex
    try:
        for status in ("timeout", "503"):
            direct = evaluate_automatic_rollback(provider_status=status)
            assert not direct.rollback and direct.provider_limitation == status
            outcome, _ = _collect(sandbox, provider_status=status)
            decision = _decision(outcome, provider_status=status)
            assert not outcome.evidence_complete and outcome.provider_incomplete_chunks == 1
            assert decision.rollback and "quality-evidence-incomplete" in decision.reasons
            assert decision.provider_limitation == status
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_missing_baseline_fails_closed_without_invented_score() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage0841_baseline" / uuid.uuid4().hex
    try:
        outcome, _ = _collect(sandbox)
        shutil.rmtree(sandbox / "tests" / "literary" / "outputs" / "baseline")
        current_dir = sandbox / "current" / "Golden_Set"
        metrics = RolloutMetrics()
        source_hash = "source-hash-1"
        digest = __import__("hashlib").sha256(source_hash.encode("utf-8")).hexdigest()
        metrics.records.append({"source_hash_sha256": digest, "chunk_index": 1, "decision": "activated", "activated": True, "payload_changed": True, "blockers": []})
        outcome = collect_production_outcome(
            {"records": [{"name": "Golden_Set", "output_dir": str(current_dir)}]}, metrics,
            root=sandbox, baseline_stage="baseline",
        )
        values = rollback_quality_inputs(outcome)
        assert not outcome.evidence_complete and "baseline-coverage-incomplete" in outcome.evidence_reasons
        assert values.baseline_quality_score is None
        assert "quality-evidence-incomplete" in _decision(outcome).reasons
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_metrics_and_outcome_are_redacted_and_real_counters_replace_defaults() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage0841_metrics" / uuid.uuid4().hex
    try:
        outcome, metrics = _collect(sandbox, current_status="failed", issues=("UNSUPPORTED_DETAIL",))
        metrics.observe_quality_outcome(outcome)
        decision = _decision(outcome)
        metrics.observe_quality_rollback(evaluated=True, triggered=decision.rollback, reasons=decision.reasons)
        payload = json.dumps({"outcome": outcome.to_dict(), "metrics": metrics.to_dict()}, ensure_ascii=False)
        assert metrics.qa_failed == 1 and metrics.provider_calls_added == 0
        assert metrics.quality_evidence_complete and metrics.quality_rollback_triggered
        assert SECRET not in payload and "source-hash-1" not in payload
        assert OUTCOME_VERSION == "7.0.0-stage08.4.1"
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_disabled_report_latches_next_session_without_deleting_outputs() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage0841_latch" / uuid.uuid4().hex
    try:
        sandbox.mkdir(parents=True)
        output = sandbox / "existing.txt"
        output.write_text("keep", encoding="utf-8")
        report = sandbox / "rollback.json"
        report.write_text(json.dumps({"rollback": True, "mode": "disabled", "reasons": ["new-omission-issue"]}), encoding="utf-8")
        assert prior_rollback_reasons(report) == ("new-omission-issue",)
        controller = RollbackController()
        controller.trigger(*prior_rollback_reasons(report))
        evidence = ProductionEvidence(
            "7.0.0-stage08.1", True, "pass", "production_canary", "literary", 5,
            "7.0.0-stage08.2", True, "pass", "literary", 192,
            "7.0.0-stage08.3", True, "pass", "safe_extractive_production_canary", "literary", 5, 192,
        )
        package = {"package_id": "p", "source": {"source_hash": "hash"}, "session": {"chunk_index": 2}}
        record = apply_production_rollout(package, RolloutConfig(True, 5), evidence, controller=controller)
        assert not record.activated and "automatic-rollback-active" in record.blockers
        assert output.read_text(encoding="utf-8") == "keep"
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_te_v6_final_freeze_and_stage084_contract_remain_compatible() -> None:
    frozen = build_te_v6_release_contract()
    assert frozen.version == "6.0.0" and frozen.frozen and frozen.backward_compatible
    assert frozen.metadata["provider_calls_added"] == 0
    assert evaluate_automatic_rollback(provider_calls_added=0).rollback is False
