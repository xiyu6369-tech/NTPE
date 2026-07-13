from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

from core.adaptive_context_production_rollout import (
    MAX_ROLLOUT_PERCENT,
    ProductionEvidence,
    RollbackController,
    RolloutConfig,
    RolloutMetrics,
    STAGE08_FREEZE_CONTRACT,
    apply_production_rollout,
    deterministic_rollout_sample,
    evaluate_automatic_rollback,
    load_production_evidence,
    validate_freeze_contract,
    write_metrics_report,
)
from core.adaptive_context_production_rollout.runtime import KILL_SWITCH_ENV
from ntpe_production_translate import build_parser

ROOT = Path(__file__).resolve().parents[2]
SECRET_CONTEXT = "Alice entered the old house. Bob watched the silent garden. The storm moved closer. " * 100


def _evidence(**changes: object) -> ProductionEvidence:
    values: dict[str, object] = {
        "policy_version": "7.0.0-stage08.1", "policy_ready": True, "policy_status": "pass",
        "policy_mode": "production_canary", "policy_profile": "literary", "policy_rollout_percent": 5,
        "budget_version": "7.0.0-stage08.2", "budget_ready": True, "budget_status": "pass",
        "budget_profile": "literary", "effective_context_tokens": 192,
        "strategy_version": "7.0.0-stage08.3", "strategy_ready": True, "strategy_status": "pass",
        "strategy": "safe_extractive_production_canary", "strategy_profile": "literary",
        "strategy_rollout_percent": 5, "strategy_context_tokens": 192,
    }
    values.update(changes)
    return ProductionEvidence(**values)  # type: ignore[arg-type]


def _sampled_hash(percent: int = 5, chunk: int = 2) -> str:
    for index in range(100_000):
        value = f"source-{index}"
        if deterministic_rollout_sample(value, chunk, "literary", "7.0.0-stage08.4", percent).sampled:
            return value
    raise AssertionError("sampled key not found")


def _package(*, source_hash: str | None = None, chunk: int = 2, context: str = SECRET_CONTEXT, valid_anchor: bool = True) -> dict[str, object]:
    prompt = f"CTX\n{context}\nSRC" if valid_anchor else f"NO_ANCHOR\n{context}"
    return {
        "package_id": f"package-{chunk}",
        "session": {"chunk_index": chunk},
        "source": {"source_hash": source_hash or _sampled_hash(chunk=chunk), "chunk_text": "not retained"},
        "context": {"previous_chunk_tail": context},
        "prompt": {"system_prompt": "frozen-system", "user_prompt": prompt, "generation_rules": "frozen"},
        "model_profile": {"engine": "NVIDIA", "model": "frozen-model", "max_output_tokens": 4096},
    }


def test_default_disabled_and_rollout_boundaries() -> None:
    package = _package()
    before = copy.deepcopy(package)
    record = apply_production_rollout(package, RolloutConfig(), _evidence())
    assert record.decision == "disabled" and package == before
    assert "production-opt-in-required" in record.blockers
    for percent in (0, 1, 5, 6):
        decision = deterministic_rollout_sample("stable", 1, "literary", "7.0.0-stage08.4", percent)
        assert decision == deterministic_rollout_sample("stable", 1, "literary", "7.0.0-stage08.4", percent)
        if percent in (0, 6):
            assert decision.sampled is False
    assert MAX_ROLLOUT_PERCENT == 5


def test_deterministic_sampling_stable_across_repeated_calls() -> None:
    first = deterministic_rollout_sample("same-source", 17, "novel", "policy-v1", 5)
    for _ in range(20):
        assert deterministic_rollout_sample("same-source", 17, "novel", "policy-v1", 5) == first
    assert 0 <= first.bucket < 10_000
    assert len(first.key_sha256) == 64


def test_valid_activation_preserves_prompt_and_provider_boundaries() -> None:
    package = _package()
    before = copy.deepcopy(package)
    metrics = RolloutMetrics()
    record = apply_production_rollout(package, RolloutConfig(True, 5, "literary"), _evidence(), metrics=metrics)
    assert record.activated is True
    assert record.estimated_tokens_saved > 0
    assert record.provider_calls_added == 0 == metrics.provider_calls_added
    assert package["model_profile"] == before["model_profile"]
    assert package["prompt"]["system_prompt"] == before["prompt"]["system_prompt"]  # type: ignore[index]
    assert package["prompt"]["generation_rules"] == before["prompt"]["generation_rules"]  # type: ignore[index]
    assert package["prompt"]["user_prompt"].startswith("CTX\n")  # type: ignore[index]
    assert package["prompt"]["user_prompt"].endswith("\nSRC")  # type: ignore[index]

    shadow_package = _package()
    shadow_before = copy.deepcopy(shadow_package)
    shadow = apply_production_rollout(
        shadow_package, RolloutConfig(True, 5, "literary", validation_mode="shadow-compatible"), _evidence()
    )
    assert shadow.decision == "shadow-compatible"
    assert shadow_package == shadow_before


def test_profile_policy_budget_strategy_and_evidence_fail_closed() -> None:
    cases = (
        (RolloutConfig(True, 5, "fast"), _evidence(), "profile-not-allowed"),
        (RolloutConfig(True, 5, "literary"), _evidence(policy_ready=False), "activation-policy-not-ready"),
        (RolloutConfig(True, 5, "literary"), _evidence(budget_ready=False), "profile-budget-not-ready"),
        (RolloutConfig(True, 5, "literary"), _evidence(strategy_ready=False), "strategy-not-ready"),
        (RolloutConfig(True, 5, "literary"), _evidence(evidence_fresh=False), "stale-evidence"),
    )
    for config, evidence, blocker in cases:
        package = _package()
        before = copy.deepcopy(package)
        record = apply_production_rollout(package, config, evidence)
        assert record.activated is False and package == before
        assert blocker in record.blockers


def test_anchor_mismatch_and_no_token_reduction_fallback_without_partial_merge() -> None:
    controller = RollbackController()
    broken = _package(valid_anchor=False)
    original = copy.deepcopy(broken)
    record = apply_production_rollout(broken, RolloutConfig(True, 5, "literary"), _evidence(), controller=controller)
    assert record.fallback_used and broken == original
    assert any("anchor" in reason for reason in record.blockers)

    short = _package(context="tiny")
    original_short = copy.deepcopy(short)
    record = apply_production_rollout(short, RolloutConfig(True, 5, "literary"), _evidence())
    assert record.fallback_used and short == original_short
    assert "no-token-reduction" in record.blockers or "ace-admission-failed" in record.blockers


def test_kill_switch_blocks_next_chunk_and_latches_rollback() -> None:
    prior = os.environ.get(KILL_SWITCH_ENV)
    controller = RollbackController()
    try:
        os.environ.pop(KILL_SWITCH_ENV, None)
        first = apply_production_rollout(_package(chunk=2), RolloutConfig(True, 5, "literary"), _evidence(), controller=controller)
        assert first.activated
        os.environ[KILL_SWITCH_ENV] = "1"
        second = apply_production_rollout(_package(chunk=3), RolloutConfig(True, 5, "literary"), _evidence(), controller=controller)
        assert not second.activated and "kill-switch-enabled" in second.blockers
        os.environ.pop(KILL_SWITCH_ENV, None)
        third = apply_production_rollout(_package(chunk=4), RolloutConfig(True, 5, "literary"), _evidence(), controller=controller)
        assert "automatic-rollback-active" in third.blockers
    finally:
        if prior is None:
            os.environ.pop(KILL_SWITCH_ENV, None)
        else:
            os.environ[KILL_SWITCH_ENV] = prior


def test_automatic_rollback_quality_and_provider_separation() -> None:
    for kwargs, reason in (
        ({"new_issues": ("OMISSION",)}, "new-omission-issue"),
        ({"new_issues": ("UNSUPPORTED_DETAIL",)}, "new-unsupported-detail-issue"),
        ({"quality_score": 79, "baseline_quality_score": 80}, "quality-score-regression"),
        ({"qa_failure_rate": .2, "baseline_qa_failure_rate": .1}, "qa-failure-rate-regression"),
        ({"provider_calls_added": 1}, "provider-calls-added"),
        ({"anchor_mismatch": True}, "payload-anchor-mismatch"),
        ({"replacement_count": 2}, "unexpected-context-replacement-count"),
        ({"metrics_complete": False}, "metrics-missing"),
        ({"evidence_match": False}, "evidence-mismatch"),
        ({"artifact_integrity": False}, "production-artifact-integrity-failure"),
    ):
        decision = evaluate_automatic_rollback(**kwargs)
        assert decision.rollback and reason in decision.reasons and decision.mode == "disabled"
    for status in ("timeout", "503"):
        decision = evaluate_automatic_rollback(provider_status=status)
        assert not decision.rollback and decision.provider_limitation == status


def test_metrics_schema_and_audit_redaction() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage084_metrics" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=False)
    try:
        metrics = RolloutMetrics()
        audit = sandbox / "audit.jsonl"
        record = apply_production_rollout(_package(), RolloutConfig(True, 5, "literary"), _evidence(), metrics=metrics, audit_path=audit)
        path = write_metrics_report(metrics, sandbox / "metrics.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        required = {
            "total_packages", "eligible_packages", "sampled_packages", "activated_packages", "fallback_packages",
            "disabled_packages", "kill_switch_blocks", "policy_blocks", "strategy_blocks", "budget_blocks",
            "anchor_blocks", "admission_blocks", "baseline_context_tokens", "ace_context_tokens",
            "estimated_tokens_saved", "estimated_reduction_ratio", "payload_changed_records",
            "payload_unchanged_records", "provider_calls_added", "qa_accepted", "qa_retry_required", "qa_failed",
            "provider_timeout", "provider_503", "rollout_bucket", "rollout_percent", "policy_version", "strategy_version",
        }
        assert required <= payload.keys()
        combined = path.read_text(encoding="utf-8") + audit.read_text(encoding="utf-8")
        assert SECRET_CONTEXT not in combined
        assert "not retained" not in combined
        assert record.provider_calls_added == 0
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_evidence_loader_rejects_stale_malformed_and_plaintext() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage084_evidence" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=False)
    try:
        policy = sandbox / "policy.json"; budget = sandbox / "budget.json"; strategy = sandbox / "strategy.json"
        policy.write_text(json.dumps({"version":"7.0.0-stage08.1","ready":True,"status":"pass","mode":"production_canary","profile":"literary","rollout_percent":5}), encoding="utf-8")
        budget.write_text(json.dumps({"version":"7.0.0-stage08.2","ready":True,"status":"pass","profile":"literary","effective_context_tokens":192}), encoding="utf-8")
        strategy.write_text(json.dumps({"version":"7.0.0-stage08.3","ready":True,"status":"pass","strategy":"safe_extractive_production_canary","profile":"literary","rollout_percent":5,"effective_context_tokens":192}), encoding="utf-8")
        loaded = load_production_evidence(policy, budget, strategy)
        assert loaded.evidence_integrity and loaded.evidence_fresh
        old = time.time() - 700_000
        for path in (policy, budget, strategy): os.utime(path, (old, old))
        assert "stale-evidence" in load_production_evidence(policy, budget, strategy).blockers
        strategy.write_text("[]", encoding="utf-8")
        try:
            load_production_evidence(policy, budget, strategy)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed evidence accepted")
        strategy.write_text(json.dumps({"version":"7.0.0-stage08.3","ready":True,"status":"pass","strategy":"safe_extractive_production_canary","profile":"literary","rollout_percent":5,"effective_context_tokens":192,"prompt":"SECRET"}), encoding="utf-8")
        assert "unsafe-evidence-payload" in load_production_evidence(policy, budget, strategy, max_age_seconds=1_000_000).blockers
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_cli_configuration_and_freeze_contract() -> None:
    parser = build_parser()
    args = parser.parse_args([
        "regression", "--ace-production-rollout", "--ace-production-rollout-percent", "5",
        "--ace-production-policy-report", "policy.json", "--ace-production-budget-report", "budget.json",
        "--ace-production-strategy-report", "strategy.json", "--ace-production-metrics-report", "metrics.json",
        "--ace-production-rollback-report", "rollback.json", "--ace-production-kill-switch",
    ])
    assert args.ace_production_rollout and args.ace_production_kill_switch
    assert validate_freeze_contract() == ()
    assert STAGE08_FREEZE_CONTRACT["maximum_rollout_percent"] == 5
    assert STAGE08_FREEZE_CONTRACT["provider_calls_added"] == 0
    assert STAGE08_FREEZE_CONTRACT["te_v6_backward_compatible"] is True
    assert STAGE08_FREEZE_CONTRACT["te_v7_final_release"] is False


def test_production_validation_harness_assembly_only() -> None:
    token = uuid.uuid4().hex
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage084_cli" / token
    stage = f"TE_V7_STAGE084_TEST_{token}"
    output_stage = ROOT / "tests" / "literary" / "outputs" / stage
    sandbox.mkdir(parents=True, exist_ok=False)
    try:
        policy = sandbox / "policy.json"; budget = sandbox / "budget.json"; strategy = sandbox / "strategy.json"
        metrics = sandbox / "metrics.json"; rollback = sandbox / "rollback.json"
        policy.write_text(json.dumps({"version":"7.0.0-stage08.1","ready":True,"status":"pass","mode":"production_canary","profile":"literary","rollout_percent":5}), encoding="utf-8")
        budget.write_text(json.dumps({"version":"7.0.0-stage08.2","ready":True,"status":"pass","profile":"literary","effective_context_tokens":192}), encoding="utf-8")
        strategy.write_text(json.dumps({"version":"7.0.0-stage08.3","ready":True,"status":"pass","strategy":"safe_extractive_production_canary","profile":"literary","rollout_percent":5,"effective_context_tokens":192}), encoding="utf-8")
        command = [
            sys.executable, "launcher_translate.py", "regression", "--set", "smoke", "--stage", stage,
            "--dry-run", "--no-evaluate", "--overwrite", "--ace-production-rollout",
            "--ace-production-validation-mode", "assembly-only", "--ace-production-rollout-percent", "5",
            "--ace-production-policy-report", str(policy), "--ace-production-budget-report", str(budget),
            "--ace-production-strategy-report", str(strategy), "--ace-production-metrics-report", str(metrics),
            "--ace-production-rollback-report", str(rollback),
        ]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        metrics_payload = json.loads(metrics.read_text(encoding="utf-8"))
        rollback_payload = json.loads(rollback.read_text(encoding="utf-8"))
        assert metrics_payload["total_packages"] > 0
        assert metrics_payload["provider_calls_added"] == 0
        assert rollback_payload["rollback"] is False
        assert "provider request start" not in result.stdout.lower()
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
        shutil.rmtree(output_stage, ignore_errors=True)
