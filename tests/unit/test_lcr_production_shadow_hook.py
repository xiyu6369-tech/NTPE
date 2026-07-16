from __future__ import annotations

import json
import threading
import time
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import core.lcr_production_shadow_hook as lcr
import core.lcr_production_shadow_hook.hook as hook_module


ENABLED = {"LCR_SHADOW_ENABLED": True, "LCR_KILL_SWITCH": False}


def package(**changes):
    value = {
        "package_id": "TXT_fixture_000001",
        "project": {"source_language": "ja", "target_language": "zh-Hant"},
        "session": {"session_id": "TXT_fixture", "chunk_index": 1, "resume_key": "fixture:1"},
        "source": {"source_hash": "a" * 40, "chunk_text": "SENSITIVE-SOURCE-CONTENT"},
        "prompt": {"system_prompt": "SENSITIVE-SYSTEM-PROMPT", "user_prompt": "SENSITIVE-USER-PROMPT"},
        "model_profile": {"engine": "NVIDIA", "model": "baseline-model"},
        "context": {"previous_chunk_tail": "SENSITIVE-CONTEXT"},
        "knowledge": {"locked_dictionary": {"a": "b"}},
        "qa_requirements": {"quality": True},
        "runtime": {"speed": "balanced"},
        "raw_provider_request": "FORBIDDEN-RAW-REQUEST",
        "raw_provider_response": "FORBIDDEN-RAW-RESPONSE",
        "authorization_header": "FORBIDDEN-AUTHORIZATION",
    }
    value.update(changes)
    return value


def test_default_off_missing_and_invalid_flags_fail_closed(monkeypatch):
    monkeypatch.delenv("LCR_SHADOW_ENABLED", raising=False)
    monkeypatch.delenv("LCR_KILL_SWITCH", raising=False)
    assert lcr.run_read_only_lcr_shadow_hook(package()).status == "blocked"
    assert lcr.run_read_only_lcr_shadow_hook(package(), feature_flags={"LCR_KILL_SWITCH": False}).status == "skipped"
    invalid = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags={"LCR_SHADOW_ENABLED": "invalid", "LCR_KILL_SWITCH": "invalid"})
    assert invalid.status == "blocked" and invalid.baseline_continues


def test_explicit_enable_runs_only_minimal_modules_and_preserves_all_identities():
    item = package()
    before = json.dumps(item, sort_keys=True)
    sink = lcr.InMemoryEvidenceSink()
    outcome = lcr.run_read_only_lcr_shadow_hook(item, feature_flags=ENABLED, evidence_sink=sink,
                                                created_at_factory=lambda: "2026-07-16T00:00:00Z")
    assert outcome.status == "completed" and outcome.baseline_continues
    assert json.dumps(item, sort_keys=True) == before
    assert outcome.before_hash == outcome.after_hash
    assert outcome.prompt_before_hash == outcome.prompt_after_hash
    assert outcome.provider_identity_before == outcome.provider_identity_after
    assert outcome.resume_before_hash == outcome.resume_after_hash
    assert outcome.output_contract_before_hash == outcome.output_contract_after_hash
    assert len(sink.records) == 1
    evidence = sink.records[0]
    assert evidence.modules_evaluated == ("chunk_cache", "multilingual_profile", "provider_routing")
    assert evidence.provider_requests_executed == 0
    assert not evidence.production_output_changed and not evidence.baseline_changed
    with pytest.raises(FrozenInstanceError):
        evidence.shadow_status = "changed"


def test_character_context_dual_pass_and_semantic_modules_never_run():
    evidence = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED, evidence_sink=lcr.InMemoryEvidenceSink()).evidence
    assert evidence is not None
    assert set(evidence.modules_evaluated).isdisjoint({
        "character_memory", "context_scene", "dual_pass", "semantic_verification"
    })


def test_identity_does_not_depend_on_created_at():
    first = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED,
                                             created_at_factory=lambda: "2026-01-01T00:00:00Z")
    second = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED,
                                              created_at_factory=lambda: "2030-01-01T00:00:00Z")
    assert first.evidence and second.evidence
    assert first.evidence.input_fingerprint == second.evidence.input_fingerprint
    assert first.evidence.hook_id == second.evidence.hook_id


def test_real_blocking_runner_returns_before_hard_deadline_and_discards_late_result(monkeypatch):
    assert lcr.wait_for_shadow_idle(1.0)
    original = hook_module.run_lcr_production_shadow
    sink = lcr.InMemoryEvidenceSink()

    def blocking(*args, **kwargs):
        time.sleep(0.2)
        return original(*args, **kwargs)

    monkeypatch.setattr(hook_module, "run_lcr_production_shadow", blocking)
    started = time.perf_counter()
    result = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED, evidence_sink=sink)
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert elapsed_ms < 50  # 25 ms hard budget plus explicit CI scheduling tolerance
    assert result.status == "timed_out" and result.baseline_continues
    assert result.result_discarded and result.evidence and result.evidence.result_discarded
    assert "hard_timeout_budget_exceeded" in result.warning_codes
    assert sink.records == []
    assert lcr.wait_for_shadow_idle(1.0)
    assert sink.records == []


def test_event_block_late_result_cannot_write_evidence_and_followup_is_busy_safe(monkeypatch):
    assert lcr.wait_for_shadow_idle(1.0)
    original = hook_module.run_lcr_production_shadow
    entered = threading.Event()
    release = threading.Event()
    sink = lcr.InMemoryEvidenceSink()

    def blocking(*args, **kwargs):
        entered.set()
        release.wait(1.0)
        return original(*args, **kwargs)

    monkeypatch.setattr(hook_module, "run_lcr_production_shadow", blocking)
    first = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED, evidence_sink=sink)
    assert entered.is_set() and first.status == "timed_out"
    follow_started = time.perf_counter()
    followup = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED, evidence_sink=sink)
    assert (time.perf_counter() - follow_started) * 1000 < 25
    assert followup.status == "degraded" and "shadow_worker_busy" in followup.warning_codes
    release.set()
    assert lcr.wait_for_shadow_idle(1.0)
    assert sink.records == []
    snapshot = lcr.executor_snapshot()
    assert snapshot.late_results_discarded >= 1 and snapshot.worker_count == 1 and snapshot.worker_daemon


def test_one_hundred_blocking_calls_keep_worker_and_queue_bounded(monkeypatch):
    assert lcr.wait_for_shadow_idle(1.0)
    original = hook_module.run_lcr_production_shadow
    entered = threading.Event()
    release = threading.Event()

    def blocking(*args, **kwargs):
        entered.set()
        release.wait(1.0)
        return original(*args, **kwargs)

    monkeypatch.setattr(hook_module, "run_lcr_production_shadow", blocking)
    before = lcr.executor_snapshot()
    latencies = []
    outcomes = []
    for _ in range(100):
        started = time.perf_counter()
        outcomes.append(lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED))
        latencies.append((time.perf_counter() - started) * 1000)
    during = lcr.executor_snapshot()
    assert entered.is_set()
    assert outcomes[0].status == "timed_out"
    assert all(item.status in {"timed_out", "degraded"} and item.baseline_continues for item in outcomes)
    assert max(latencies) < 50
    assert during.worker_count == 1 and during.worker_daemon
    assert during.queue_capacity == 1 and during.queue_depth <= 1 and during.in_flight
    assert during.accepted - before.accepted == 1
    assert during.rejected_busy - before.rejected_busy >= 99
    release.set()
    assert lcr.wait_for_shadow_idle(1.0)


class BrokenSink:
    def write(self, evidence):
        raise OSError("synthetic sink failure")


def test_evidence_sink_failure_is_isolated():
    result = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED, evidence_sink=BrokenSink())
    assert result.status == "degraded" and result.baseline_continues
    assert "evidence_sink_exception" in result.warning_codes
    assert result.evidence and result.evidence.provider_requests_executed == 0


@pytest.mark.parametrize("target", ["resolve_hook_flags", "_extract_metadata", "run_lcr_production_shadow", "_minimal_overrides", "_canonical_hash"])
def test_hook_internal_exceptions_never_escape(monkeypatch, target):
    def broken(*args, **kwargs):
        raise RuntimeError(f"synthetic {target} failure")
    monkeypatch.setattr(hook_module, target, broken)
    result = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED)
    assert result.status in {"blocked", "degraded", "invalid"}
    assert result.baseline_continues
    assert result.evidence is None or result.evidence.provider_requests_executed == 0


def test_profile_selection_exception_is_degraded_by_batch10_runner(monkeypatch):
    def overrides(metadata):
        return {"multilingual_profile": lambda _: (_ for _ in ()).throw(RuntimeError("profile failure"))}
    monkeypatch.setattr(hook_module, "_minimal_overrides", overrides)
    result = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED)
    assert result.status == "degraded" and result.baseline_continues
    assert result.evidence and "multilingual_profile_degraded" in result.evidence.warnings


def test_routing_plan_exception_is_degraded_by_batch10_runner(monkeypatch):
    def overrides(metadata):
        return {"provider_routing": lambda _: (_ for _ in ()).throw(RuntimeError("routing failure"))}
    monkeypatch.setattr(hook_module, "_minimal_overrides", overrides)
    result = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED)
    assert result.status == "degraded" and result.baseline_continues
    assert result.evidence and "provider_routing_degraded" in result.evidence.warnings


def test_atomic_file_sink_enforces_root_and_writes_redacted_evidence(tmp_path: Path):
    target = tmp_path / "evidence" / "hook.json"
    sink = lcr.AtomicTestFileEvidenceSink(target, allowed_root=tmp_path)
    result = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED, evidence_sink=sink,
                                               created_at_factory=lambda: "2026-07-16T00:00:00Z")
    assert result.status == "completed" and target.exists()
    text = target.read_text(encoding="utf-8")
    for secret in ("SENSITIVE-SOURCE-CONTENT", "SENSITIVE-USER-PROMPT", "FORBIDDEN-RAW-REQUEST", "FORBIDDEN-AUTHORIZATION"):
        assert secret not in text
    with pytest.raises(ValueError):
        lcr.AtomicTestFileEvidenceSink(tmp_path.parent / "escape.json", allowed_root=tmp_path).write(result.evidence)


def test_file_sink_rejects_symlink_escape(monkeypatch, tmp_path: Path):
    target = tmp_path / "linked" / "evidence.json"
    sink = lcr.AtomicTestFileEvidenceSink(target, allowed_root=tmp_path)
    monkeypatch.setattr(Path, "is_symlink", lambda self: self.name == "linked")
    evidence = lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED).evidence
    assert evidence is not None
    with pytest.raises(ValueError):
        sink.write(evidence)


def test_activation_gate_fails_closed_and_never_authorizes_active_production():
    names = (
        "single_hook_only", "hook_default_disabled", "kill_switch_default_enabled",
        "baseline_hash_unchanged", "prompt_identity_unchanged", "provider_identity_unchanged",
        "resume_unchanged", "output_unchanged", "provider_requests_zero", "network_requests_zero",
        "hook_exceptions_isolated", "timeout_budget_pass", "blocking_runner_test_passed",
        "caller_deadline_enforced", "late_result_discarded", "worker_count_bounded", "queue_bounded",
        "production_files_within_limit",
        "security_pass", "all_regressions_pass", "manual_approval_present",
    )
    ready = {name: True for name in names}
    assert lcr.evaluate_extended_shadow_gate({}).status == "insufficient_evidence"
    assert lcr.evaluate_extended_shadow_gate({**ready, "provider_requests_zero": False}).status == "not_ready"
    gate = lcr.evaluate_extended_shadow_gate(ready)
    assert gate.status == "ready_for_extended_shadow" and not gate.active_production_authorized


def test_hundred_calls_are_deterministic_and_provider_free():
    outcomes = [lcr.run_read_only_lcr_shadow_hook(package(), feature_flags=ENABLED,
                                                 created_at_factory=lambda: "fixed") for _ in range(100)]
    assert len({item.evidence.input_fingerprint for item in outcomes if item.evidence}) == 1
    assert all(item.evidence and item.evidence.provider_requests_executed == 0 for item in outcomes)
