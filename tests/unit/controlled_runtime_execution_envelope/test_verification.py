"""Tests for Stage 6.4 verification API."""

import hashlib
import os
import threading
from dataclasses import replace

import pytest

from core.controlled_runtime_execution_envelope.verification import (
    verify_execution_envelope,
)
from core.controlled_runtime_execution_envelope.models import (
    ControlledRuntimeExecutionEnvelope,
    ControlledRuntimeExecutionEnvelopeResult,
)


def _fp(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _make_authentic_envelope() -> ControlledRuntimeExecutionEnvelope:
    chain = tuple(_fp(f"layer{i}") for i in range(14))
    return ControlledRuntimeExecutionEnvelope(
        envelope_id="env-001",
        claim_id="claim-001",
        consumption_id="cons-001",
        authorization_id="auth-001",
        authorization_request_fingerprint=_fp("ar"),
        authorization_decision_fingerprint=_fp("ad"),
        execution_plan_fingerprint=_fp("ep"),
        stage62_request_fingerprint=_fp("62r"),
        stage62_record_fingerprint=_fp("62c"),
        stage63_claim_request_fingerprint=_fp("63cr"),
        stage63_claim_fingerprint=_fp("63c"),
        selected_adapter_index=0,
        execution_unit_count=1,
        authorization_consumption_prepared=True,
        authorization_consumed=True,
        authorization_reusable=False,
        durable_reuse_prevention_established=True,
        persistent_registry_written=True,
        runtime_handoff_prepared=True,
        runtime_handoff_completed=False,
        execution_started=False,
        execution_completed=False,
        runtime_execution_enabled=False,
        provider_execution_enabled=False,
        network_execution_enabled=False,
        translation_execution_enabled=False,
        output_write_enabled=False,
        resume_write_enabled=False,
        cache_write_enabled=False,
        retry_enabled=False,
        fallback_enabled=False,
        production_hook_enabled=False,
        execution_mode="controlled_single_execution",
        envelope_state="runtime_handoff_prepared_not_executed",
        upstream_fingerprint_chain=chain,
        envelope_request_fingerprint=_fp("req-fp"),
    )


# ---------------------------------------------------------------------------
# Success
# ---------------------------------------------------------------------------


def test_authentic_envelope_verifies():
    env = _make_authentic_envelope()
    result = verify_execution_envelope(env)
    assert result.status == "runtime_handoff_prepared_not_executed"


# ---------------------------------------------------------------------------
# Tampered fingerprint
# ---------------------------------------------------------------------------


def test_tampered_envelope_fingerprint_fails():
    env = _make_authentic_envelope()
    # Override envelope_fingerprint to a wrong value to simulate tampering
    object.__setattr__(env, "envelope_fingerprint", _fp("wrong-fingerprint"))
    result = verify_execution_envelope(env)
    assert result.status == "verification_failed"


# ---------------------------------------------------------------------------
# State field violations
# ---------------------------------------------------------------------------


def test_wrong_envelope_state_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, envelope_state="executed")
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_wrong_execution_mode_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, execution_mode="batch_execution")
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_authorization_consumed_false_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, authorization_consumed=False)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_authorization_reusable_true_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, authorization_reusable=True)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_durable_prevention_false_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, durable_reuse_prevention_established=False)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_registry_written_false_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, persistent_registry_written=False)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_runtime_handoff_prepared_false_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, runtime_handoff_prepared=False)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_runtime_handoff_completed_true_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, runtime_handoff_completed=True)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_execution_started_true_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, execution_started=True)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_execution_completed_true_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, execution_completed=True)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


# ---------------------------------------------------------------------------
# Enablement violations
# ---------------------------------------------------------------------------


def test_runtime_enabled_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, runtime_execution_enabled=True)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_provider_enabled_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, provider_execution_enabled=True)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_network_enabled_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, network_execution_enabled=True)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_translation_enabled_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, translation_execution_enabled=True)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_output_enabled_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, output_write_enabled=True)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_resume_enabled_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, resume_write_enabled=True)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_cache_enabled_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, cache_write_enabled=True)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_retry_enabled_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, retry_enabled=True)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_fallback_enabled_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, fallback_enabled=True)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_production_hook_enabled_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, production_hook_enabled=True)
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


# ---------------------------------------------------------------------------
# Chain violations
# ---------------------------------------------------------------------------


def test_upstream_chain_length_wrong_fails():
    env = _make_authentic_envelope()
    tampered = replace(env, upstream_fingerprint_chain=tuple(_fp(f"L{i}") for i in range(10)))
    result = verify_execution_envelope(tampered)
    assert result.status == "verification_failed"


def test_chain_exactly_15():
    env = _make_authentic_envelope()
    assert len(env.upstream_fingerprint_chain) == 15  # 14 upstream + 1 envelope


# ---------------------------------------------------------------------------
# Determinism and safety
# ---------------------------------------------------------------------------


def test_repeated_verification_deterministic():
    env = _make_authentic_envelope()
    r1 = verify_execution_envelope(env)
    r2 = verify_execution_envelope(env)
    assert r1.status == r2.status
    assert r1.result_fingerprint == r2.result_fingerprint


def test_verification_does_not_mutate_envelope():
    env = _make_authentic_envelope()
    fp_before = env.envelope_fingerprint
    _ = verify_execution_envelope(env)
    assert env.envelope_fingerprint == fp_before


def test_verification_no_filesystem_writes():
    env = _make_authentic_envelope()
    start = set(os.listdir("."))
    _ = verify_execution_envelope(env)
    end = set(os.listdir("."))
    assert start == end


def test_verification_no_threads():
    env = _make_authentic_envelope()
    pre = threading.active_count()
    _ = verify_execution_envelope(env)
    post = threading.active_count()
    assert pre == post