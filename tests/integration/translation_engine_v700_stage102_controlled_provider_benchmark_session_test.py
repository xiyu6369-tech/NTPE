from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from pathlib import Path

from core.adaptive_context_provider_benchmark_session import (
    SESSION_VERSION, ControlledProviderBenchmarkSession, ControlledSessionConfig,
    ProviderAttemptPlan, verify_session_report, write_session_report,
)
from core.adaptive_context_provider_evidence import (
    ProviderEvidenceCollector, ProviderEvidenceConfig, ProviderRequestIdentity,
    load_provider_evidence, write_provider_evidence,
)

ROOT = Path(__file__).resolve().parents[2]


def _config(**changes: object) -> ControlledSessionConfig:
    values = {"enabled": True, "pair_id": "stage102-pair", "run_kind": "baseline", "execution_mode": "mock", "real_provider_execution": False}
    values.update(changes)
    return ControlledSessionConfig(**values)  # type: ignore[arg-type]


def _identity(**changes: object) -> ProviderRequestIdentity:
    values = {
        "pair_id": "stage102-pair", "run_kind": "baseline", "set_name": "Smoke_Set", "chunk_index": 1,
        "source_hash": "a" * 64, "chunk_hash": "b" * 64, "model": "model-a", "attempt": 1,
    }
    values.update(changes)
    return ProviderRequestIdentity(**values)  # type: ignore[arg-type]


def _plan(attempt: int = 1, **changes: object) -> ProviderAttemptPlan:
    values = {"attempt": attempt, "model": "model-a", "timeout_seconds": 180, "estimated_input_tokens": 100, "estimated_output_tokens": 80}
    values.update(changes)
    return ProviderAttemptPlan(**values)  # type: ignore[arg-type]


def _payload() -> dict[str, object]:
    return {"prompt": {"system_prompt": "SECRET-SYSTEM", "user_prompt": "SECRET-USER"}, "source": {"source_text": "SECRET-SOURCE"}, "model_profile": {"model": "model-a"}}


class SequenceProvider:
    def __init__(self, *results: dict[str, object], mutate: bool = False) -> None:
        self.results = list(results); self.calls = 0; self.mutate = mutate

    def __call__(self, payload: dict[str, object], plan: ProviderAttemptPlan) -> dict[str, object]:
        self.calls += 1
        if self.mutate:
            payload["prompt"] = {"user_prompt": "MUTATED"}
            payload["new_field"] = "MUTATED"
        return dict(self.results[min(self.calls - 1, len(self.results) - 1)])


def _run(provider: SequenceProvider, *, identity: ProviderRequestIdentity | None = None, plans: tuple[ProviderAttemptPlan, ...] | None = None, config: ControlledSessionConfig | None = None):
    return ControlledProviderBenchmarkSession(config or _config()).run(
        identity=identity or _identity(), payload=_payload(), plans=plans or (_plan(),), provider=provider,
    )


def test_default_disabled_fails_closed() -> None:
    session = ControlledProviderBenchmarkSession(ControlledSessionConfig())
    try: session.run(identity=_identity(), payload=_payload(), plans=(_plan(),), provider=SequenceProvider({"status": "success"}))
    except ValueError as exc: assert "explicit-opt-in" in str(exc)
    else: raise AssertionError("disabled session ran")


def test_real_execution_requires_matching_flag() -> None:
    for config in (_config(execution_mode="real"), _config(execution_mode="mock", real_provider_execution=True)):
        try: ControlledProviderBenchmarkSession(config).run(identity=_identity(), payload=_payload(), plans=(_plan(),), provider=SequenceProvider({"status": "success"}))
        except ValueError: pass
        else: raise AssertionError("execution provenance mismatch accepted")


def test_attempt_plan_is_required() -> None:
    try: ControlledProviderBenchmarkSession(_config()).run(identity=_identity(), payload=_payload(), plans=(), provider=SequenceProvider({"status": "success"}))
    except ValueError as exc: assert "attempt-plan-required" in str(exc)
    else: raise AssertionError("empty plan accepted")


def test_attempt_plan_order_is_caller_owned_and_strict() -> None:
    try: _run(SequenceProvider({"status": "success"}), plans=(_plan(2),))
    except ValueError as exc: assert "plan-order-invalid" in str(exc)
    else: raise AssertionError("misordered plan accepted")


def test_single_success_attempt_evidence() -> None:
    result = _run(SequenceProvider({"status": "success", "usage": {"input_tokens": 100, "output_tokens": 80}}))
    assert result.summary.state == "completed" and result.summary.attempts_executed == 1
    assert len(result.evidence.records) == 1 and result.evidence.records[0].timing_complete


def test_timeout_attempt_is_provider_limited() -> None:
    result = _run(SequenceProvider({"status": "failed", "error": "request timed out"}))
    assert result.summary.state == "provider_limited" and result.summary.timeout_attempts == 1
    assert result.evidence.records[0].external_provider_condition


def test_http_503_attempt_is_provider_limited() -> None:
    result = _run(SequenceProvider({"status": "failed", "error": "unavailable", "http_status": 503}))
    assert result.summary.state == "provider_limited" and result.summary.http_503_attempts == 1


def test_provider_exception_keeps_sanitized_attempt_evidence() -> None:
    def raises_timeout(payload: dict[str, object], plan: ProviderAttemptPlan) -> dict[str, object]:
        raise TimeoutError("SECRET provider details")
    result = ControlledProviderBenchmarkSession(_config()).run(
        identity=_identity(), payload=_payload(), plans=(_plan(),), provider=raises_timeout,
    )
    assert result.summary.state == "provider_limited"
    assert result.evidence.records[0].error_category == "timeout"
    assert "SECRET" not in json.dumps(result.to_dict(), ensure_ascii=False)


def test_retry_attempts_are_independent() -> None:
    provider = SequenceProvider({"status": "failed", "error": "timeout"}, {"status": "success"})
    result = _run(provider, plans=(_plan(1), _plan(2)))
    assert [row.attempt for row in result.evidence.records] == [1, 2]
    assert provider.calls == 2 and result.summary.attempts_executed == 2


def test_retry_latency_is_accumulated() -> None:
    result = _run(SequenceProvider({"status": "failed", "error": "timeout"}, {"status": "success"}), plans=(_plan(1), _plan(2)))
    assert result.summary.total_latency_ms == round(sum(row.elapsed_ms or 0 for row in result.evidence.records), 3)


def test_first_failure_second_success_completes() -> None:
    result = _run(SequenceProvider({"status": "failed", "error": "timeout"}, {"status": "success"}), plans=(_plan(1), _plan(2)))
    assert result.summary.state == "completed"
    assert result.summary.failed_attempts == 1 and result.summary.successful_attempts == 1


def test_all_external_attempts_failed_are_provider_limited() -> None:
    result = _run(SequenceProvider({"status": "failed", "error": "timeout"}, {"status": "failed", "http_status": 503, "error": "unavailable"}), plans=(_plan(1), _plan(2)))
    assert result.summary.state == "provider_limited" and result.summary.failed_attempts == 2


def test_non_external_failed_attempt_is_failed() -> None:
    result = _run(SequenceProvider({"status": "failed"}))
    assert result.summary.state == "failed"


def test_mock_provider_cannot_be_ready() -> None:
    result = _run(SequenceProvider({"status": "success"}))
    assert result.evidence.status == "evidence_complete_mock_only"
    assert not result.evidence.ready_for_benchmark


def test_resume_chunk_excluded_without_provider_call() -> None:
    provider = SequenceProvider({"status": "success"})
    result = _run(provider, identity=_identity(resumed=True))
    assert result.summary.state == "excluded" and provider.calls == 0
    assert result.evidence.excluded_resume_chunks and not result.evidence.records


def test_suspicious_short_output_blocks_evidence_readiness() -> None:
    result = _run(SequenceProvider({"status": "success", "usage": {"output_tokens": 10}}), identity=_identity(minimum_output_tokens=50))
    assert "suspicious-short-output" in result.evidence.limitations
    assert not result.evidence.ready_for_benchmark


def test_missing_provider_usage_uses_caller_estimate() -> None:
    result = _run(SequenceProvider({"status": "success"}))
    usage = result.evidence.records[0].token_usage
    assert usage.usage_source == "estimate" and usage.estimated_input_tokens == 100 and usage.estimated_output_tokens == 80


def test_provider_failure_is_decoupled_from_quality() -> None:
    result = _run(SequenceProvider({"status": "failed", "error": "timeout"}))
    assert result.summary.provider_failure_decoupled is True
    assert result.summary.readiness_evaluated is False
    assert "session-does-not-evaluate-stage10-readiness" in result.limitations


def test_payload_and_prompt_are_preserved_when_provider_mutates_copy() -> None:
    payload = _payload(); before = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    result = ControlledProviderBenchmarkSession(_config()).run(identity=_identity(), payload=payload, plans=(_plan(),), provider=SequenceProvider({"status": "success"}, mutate=True))
    assert json.dumps(payload, ensure_ascii=False, sort_keys=True) == before
    assert result.summary.payload_preserved and result.summary.prompt_preserved and not result.blockers


def test_session_report_redaction_and_integrity() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage102_report" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=False)
    try:
        result = _run(SequenceProvider({"status": "success", "content": "SECRET-PROVIDER-BODY"}))
        path = write_session_report(result, sandbox / "session.json")
        serialized = path.read_text(encoding="utf-8")
        assert "SECRET" not in serialized and verify_session_report(path)["content_redacted"] is True
        payload = json.loads(serialized); payload["summary"]["state"] = "tampered"; path.write_text(json.dumps(payload), encoding="utf-8")
        try: verify_session_report(path)
        except ValueError: pass
        else: raise AssertionError("tampered session report accepted")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_stage101_evidence_artifact_round_trip() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage102_evidence" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=False)
    try:
        collector = ProviderEvidenceCollector(ProviderEvidenceConfig(True, "stage102-pair", "baseline", False))
        handle = collector.begin_attempt(_identity())
        collector.finish_attempt(handle, {"status": "success"})
        path = write_provider_evidence(collector.bundle(), sandbox / "evidence.json")
        assert load_provider_evidence(path) == collector.bundle()
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_stage09_and_te_v6_frozen_files_unchanged() -> None:
    targets = (
        ROOT / "tests" / "fixtures" / "te_v7_stage09" / "TE_V7_STAGE09_BASELINE.json",
        ROOT / "lts/txt_translation_runtime.py",
        ROOT / "core/translation_runtime/runtime_speed_policy.py",
    )
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in targets}
    _run(SequenceProvider({"status": "success"}))
    assert SESSION_VERSION == "7.0.0-stage10.2"
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in targets}
