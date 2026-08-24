from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from pathlib import Path

from core.adaptive_context_provider_evidence import (
    PROVIDER_EVIDENCE_VERSION, ProviderEvidenceCollector, ProviderEvidenceConfig,
    ProviderRequestIdentity, load_provider_evidence, write_provider_evidence,
)
from core.adaptive_context_provider_evidence.redaction import assert_redacted

ROOT = Path(__file__).resolve().parents[2]


def _config(**changes: object) -> ProviderEvidenceConfig:
    values = {"enabled": True, "pair_id": "stage10-pair", "run_kind": "baseline", "real_provider_execution": False}
    values.update(changes)
    return ProviderEvidenceConfig(**values)  # type: ignore[arg-type]


def _identity(**changes: object) -> ProviderRequestIdentity:
    values = {
        "pair_id": "stage10-pair", "run_kind": "baseline", "set_name": "Smoke_Set", "chunk_index": 1,
        "source_hash": "a" * 64, "chunk_hash": "b" * 64, "model": "frozen-model", "attempt": 1,
    }
    values.update(changes)
    return ProviderRequestIdentity(**values)  # type: ignore[arg-type]


def _result(**changes: object) -> dict[str, object]:
    values: dict[str, object] = {
        "status": "success", "provider_model": "frozen-model", "provider_elapsed_seconds": 0.125,
        "provider_started_at": "2026-07-14T00:00:00Z", "provider_finished_at": "2026-07-14T00:00:00.125Z",
        "estimated_input_tokens": 100, "estimated_output_tokens": 80,
    }
    values.update(changes)
    return values


def test_disabled_by_default_fails_closed() -> None:
    collector = ProviderEvidenceCollector(ProviderEvidenceConfig())
    try: collector.collect_attempt(_identity(), _result())
    except ValueError as exc: assert "explicit-opt-in" in str(exc)
    else: raise AssertionError("disabled collector accepted evidence")


def test_invalid_pair_and_run_kind_fail_closed() -> None:
    for config in (_config(pair_id="bad pair"), _config(run_kind="other")):
        try: ProviderEvidenceCollector(config).collect_attempt(_identity(), _result())
        except ValueError: pass
        else: raise AssertionError("invalid configuration accepted")


def test_existing_result_timing_adapter_is_complete() -> None:
    collector = ProviderEvidenceCollector(_config())
    record = collector.collect_attempt(_identity(), _result())
    assert record is not None and record.elapsed_ms == 125.0 and record.timing_complete
    bundle = collector.bundle()
    assert bundle.evidence_complete and not bundle.ready_for_benchmark
    assert bundle.status == "evidence_complete_mock_only"


def test_begin_finish_measures_request_boundary() -> None:
    collector = ProviderEvidenceCollector(_config())
    handle = collector.begin_attempt(_identity(), started_ns=1_000_000_000, started_at_utc="2026-07-14T00:00:00Z")
    record = collector.finish_attempt(handle, _result(provider_elapsed_seconds=None), finished_ns=1_250_000_000, finished_at_utc="2026-07-14T00:00:00.250Z")
    assert record is not None and record.elapsed_ms == 250.0 and record.timing_complete


def test_missing_timing_evidence_is_incomplete() -> None:
    collector = ProviderEvidenceCollector(_config())
    collector.collect_attempt(_identity(), _result(provider_elapsed_seconds=None, provider_started_at="", provider_finished_at=""))
    bundle = collector.bundle()
    assert not bundle.evidence_complete and "provider-timing-evidence-incomplete" in bundle.limitations


def test_timeout_is_external_provider_condition() -> None:
    collector = ProviderEvidenceCollector(_config(real_provider_execution=True))
    record = collector.collect_attempt(_identity(), _result(status="failed", error="request timed out"))
    assert record is not None and record.error_category == "timeout" and record.external_provider_condition
    assert collector.bundle().status == "evidence_complete_provider_limited"
    assert not collector.bundle().ready_for_benchmark and "provider-run-incomplete" in collector.bundle().limitations


def test_http_503_is_external_provider_condition() -> None:
    record = ProviderEvidenceCollector(_config()).collect_attempt(_identity(), _result(status="failed", error="service unavailable", http_status=503))
    assert record is not None and record.error_category == "http_503" and record.http_status == 503


def test_retry_latency_is_sum_of_request_attempts() -> None:
    collector = ProviderEvidenceCollector(_config())
    collector.collect_attempt(_identity(attempt=1), _result(status="failed", error="timeout", provider_elapsed_seconds=.1))
    collector.collect_attempt(_identity(attempt=2), _result(provider_elapsed_seconds=.2))
    assert collector.total_latency_ms() == 300.0
    assert [row.attempt for row in collector.bundle().records] == [1, 2]


def test_resume_chunk_is_excluded_without_request_evidence() -> None:
    collector = ProviderEvidenceCollector(_config())
    assert collector.collect_attempt(_identity(resumed=True), _result()) is None
    bundle = collector.bundle()
    assert not bundle.records and bundle.excluded_resume_chunks[0]["reason"] == "resume-chunk-excluded"


def test_identity_contract_mismatch_is_rejected() -> None:
    collector = ProviderEvidenceCollector(_config())
    for identity in (_identity(pair_id="other"), _identity(run_kind="candidate")):
        try: collector.collect_attempt(identity, _result())
        except ValueError as exc: assert "contract-mismatch" in str(exc)
        else: raise AssertionError("identity mismatch accepted")


def test_fallback_model_is_metadata_only() -> None:
    record = ProviderEvidenceCollector(_config()).collect_attempt(_identity(), _result(provider_model="fallback-model"))
    assert record is not None and record.model == "fallback-model" and record.fallback_used


def test_provider_token_usage_preferred_over_estimate() -> None:
    record = ProviderEvidenceCollector(_config()).collect_attempt(_identity(), _result(usage={"prompt_tokens": 101, "completion_tokens": 77}))
    assert record is not None and record.token_usage.actual_input_tokens == 101
    assert record.token_usage.actual_output_tokens == 77 and record.token_usage.usage_source == "provider"


def test_suspicious_short_output_blocks_readiness() -> None:
    collector = ProviderEvidenceCollector(_config(real_provider_execution=True))
    collector.collect_attempt(_identity(minimum_output_tokens=50), _result(usage={"output_tokens": 10}))
    bundle = collector.bundle()
    assert bundle.evidence_complete and not bundle.ready_for_benchmark
    assert "suspicious-short-output" in bundle.limitations


def test_redaction_rejects_raw_payload_fields() -> None:
    for payload in ({"source_text": "SECRET"}, {"provider_response": {"content": "SECRET"}}, {"api_key": "SECRET"}):
        try: assert_redacted(payload)
        except ValueError: pass
        else: raise AssertionError("unsafe payload accepted")


def test_artifact_sha256_detects_mutation() -> None:
    sandbox = ROOT / ".ntpe_test_sandbox" / "stage101_artifact" / uuid.uuid4().hex
    sandbox.mkdir(parents=True, exist_ok=False)
    try:
        collector = ProviderEvidenceCollector(_config())
        collector.collect_attempt(_identity(), _result())
        path = write_provider_evidence(collector.bundle(), sandbox / "evidence.json")
        loaded = load_provider_evidence(path)
        assert loaded == collector.bundle()
        payload = json.loads(path.read_text(encoding="utf-8")); payload["pair_id"] = "tampered"
        path.write_text(json.dumps(payload), encoding="utf-8")
        try: load_provider_evidence(path)
        except ValueError: pass
        else: raise AssertionError("tampered evidence accepted")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_stage09_artifacts_and_frozen_runtime_are_unchanged() -> None:
    targets = (
        ROOT / "tests" / "fixtures" / "te_v7_stage09" / "TE_V7_STAGE09_BASELINE.json",
        ROOT / "lts/txt_translation_runtime.py",
        ROOT / "core/translation_runtime/runtime_speed_policy.py",
    )
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in targets}
    collector = ProviderEvidenceCollector(_config())
    collector.collect_attempt(_identity(), _result())
    assert PROVIDER_EVIDENCE_VERSION == "7.0.0-stage10.1"
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in targets}
