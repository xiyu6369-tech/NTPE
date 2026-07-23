"""Unit tests for verify_consumption_record.

Tests tampered-record rejection and deterministic verification behavior.
Uses the public verify_consumption_record from verification.py.
"""
from __future__ import annotations

import hashlib
from dataclasses import replace

from core.controlled_runtime_authorization_consumption.models import (
    ControlledRuntimeAuthorizationConsumptionRecord,
)
from core.controlled_runtime_authorization_consumption.verification import (
    ConsumptionRecordVerificationResult,
    verify_consumption_record,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_AUTH_ID = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"


def _fake_sha256(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _make_authentic_record() -> ControlledRuntimeAuthorizationConsumptionRecord:
    """Return a minimal valid consumption record for verification.

    Builds the record with the same pattern the consumer uses:
    placeholder chain[10] → compute fingerprint → replace with corrected chain.

    Because ``upstream_fingerprint_chain`` is excluded from the fingerprint
    payload (self-reference), ``replace()`` preserves the same fingerprint.
    """
    chain_layers = [_fake_sha256(f"layer-{i}") for i in range(10)]
    chain_layers.append("")  # placeholder — filled below
    chain = tuple(chain_layers)

    record = ControlledRuntimeAuthorizationConsumptionRecord(
        consumption_id="verification-test-001",
        authorization_id=_AUTH_ID,
        authorization_request_fingerprint=_fake_sha256("auth-req"),
        authorization_decision_fingerprint=_fake_sha256("auth-dec"),
        execution_plan_fingerprint=_fake_sha256("plan"),
        selected_adapter_index=0,
        consumed_unit_count=1,
        previous_authorization_consumed=False,
        authorization_consumption_prepared=True,
        authorization_consumed=False,
        authorization_reusable=False,
        durable_reuse_prevention_established=False,
        persistent_registry_written=False,
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
        status="consumption_prepared_not_executed",
        reason_codes=(),
        upstream_fingerprint_chain=chain,
        consumption_request_fingerprint=_fake_sha256("consumption-req"),
        schema_name="ntpe.controlled_runtime_authorization_consumption_record",
        schema_version="1.0",
    )

    # Patch the record fingerprint into the chain at position 10
    corrected_chain = tuple(
        list(record.upstream_fingerprint_chain[:10]) + [record.record_fingerprint]
    )
    # replace() runs __post_init__ → fingerprint recomputed, chain excluded → same fp
    record = replace(record, upstream_fingerprint_chain=corrected_chain)
    return record


def _verify(record: ControlledRuntimeAuthorizationConsumptionRecord) -> ConsumptionRecordVerificationResult:
    """Call verify_consumption_record with record-derived expected values."""
    return verify_consumption_record(
        record,
        request_fingerprint=record.consumption_request_fingerprint,
        authorization_id=record.authorization_id,
        authorization_request_fingerprint=record.authorization_request_fingerprint,
        authorization_decision_fingerprint=record.authorization_decision_fingerprint,
        execution_plan_fingerprint=record.execution_plan_fingerprint,
        adapter_index=record.selected_adapter_index,
        unit_count=record.consumed_unit_count,
    )


def _tamper(record: ControlledRuntimeAuthorizationConsumptionRecord, **attrs):
    """Force-set attributes on a frozen record for tampering tests."""
    for key, val in attrs.items():
        object.__setattr__(record, key, val)
    return record


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_authentic_record_verifies():
    record = _make_authentic_record()
    result = _verify(record)
    assert result.valid is True, (
        f"authentic record should verify; reason_codes={result.reason_codes}"
    )


def test_tampered_record_fingerprint_fails():
    record = _make_authentic_record()
    tampered = _tamper(record, record_fingerprint=_fake_sha256("tampered-rec"))
    result = _verify(tampered)
    assert result.valid is False


def test_tampered_schema_name_fails():
    record = _make_authentic_record()
    tampered = _tamper(record, schema_name="wrong.schema")
    result = _verify(tampered)
    assert result.valid is False


def test_tampered_schema_version_fails():
    record = _make_authentic_record()
    tampered = _tamper(record, schema_version="99.0")
    result = _verify(tampered)
    assert result.valid is False


def test_tampered_authorization_id_fails():
    record = _make_authentic_record()
    tampered = replace(
        record,
        authorization_id=_fake_sha256("wrong-auth"),
    )
    result = _verify(tampered)
    assert result.valid is False


def test_tampered_auth_request_fingerprint_fails():
    record = _make_authentic_record()
    tampered = replace(
        record,
        authorization_request_fingerprint=_fake_sha256("wrong-req"),
    )
    result = _verify(tampered)
    assert result.valid is False


def test_tampered_auth_decision_fingerprint_fails():
    record = _make_authentic_record()
    tampered = replace(
        record,
        authorization_decision_fingerprint=_fake_sha256("wrong-dec"),
    )
    result = _verify(tampered)
    assert result.valid is False


def test_tampered_plan_fingerprint_fails():
    record = _make_authentic_record()
    tampered = replace(
        record,
        execution_plan_fingerprint=_fake_sha256("wrong-plan"),
    )
    result = _verify(tampered)
    assert result.valid is False


def test_tampered_adapter_index_fails():
    record = _make_authentic_record()
    tampered = replace(record, selected_adapter_index=99)
    result = _verify(tampered)
    assert result.valid is False


def test_tampered_unit_count_fails():
    record = _make_authentic_record()
    tampered = replace(record, consumed_unit_count=2)
    result = _verify(tampered)
    assert result.valid is False


def test_tampered_upstream_chain_fails():
    record = _make_authentic_record()
    tampered_chain = tuple(
        list(record.upstream_fingerprint_chain[:-1])
        + [_fake_sha256("tampered-link")]
    )
    tampered = _tamper(record, upstream_fingerprint_chain=tampered_chain)
    result = _verify(tampered)
    assert result.valid is False


def test_previous_authorization_consumed_true_fails():
    record = _make_authentic_record()
    tampered = replace(record, previous_authorization_consumed=True)
    result = _verify(tampered)
    assert result.valid is False


def test_authorization_consumed_true_fails():
    record = _make_authentic_record()
    tampered = replace(record, authorization_consumed=True)
    result = _verify(tampered)
    assert result.valid is False


def test_authorization_reusable_true_fails():
    record = _make_authentic_record()
    tampered = replace(record, authorization_reusable=True)
    result = _verify(tampered)
    assert result.valid is False


def test_false_execution_claim_fails():
    record = _make_authentic_record()
    tampered = replace(
        record,
        execution_started=True,
        execution_completed=True,
    )
    result = _verify(tampered)
    assert result.valid is False


def test_false_persistent_registry_claim_fails():
    record = _make_authentic_record()
    tampered = replace(record, persistent_registry_written=True)
    result = _verify(tampered)
    assert result.valid is False


def test_false_durable_prevention_claim_fails():
    record = _make_authentic_record()
    tampered = replace(
        record,
        durable_reuse_prevention_established=True,
    )
    result = _verify(tampered)
    assert result.valid is False


def test_runtime_enablement_true_fails():
    record = _make_authentic_record()
    tampered = replace(record, runtime_execution_enabled=True)
    result = _verify(tampered)
    assert result.valid is False


def test_provider_enablement_true_fails():
    record = _make_authentic_record()
    tampered = replace(record, provider_execution_enabled=True)
    result = _verify(tampered)
    assert result.valid is False


def test_network_enablement_true_fails():
    record = _make_authentic_record()
    tampered = replace(record, network_execution_enabled=True)
    result = _verify(tampered)
    assert result.valid is False


def test_translation_enablement_true_fails():
    record = _make_authentic_record()
    tampered = replace(record, translation_execution_enabled=True)
    result = _verify(tampered)
    assert result.valid is False


def test_output_write_enabled_true_fails():
    record = _make_authentic_record()
    tampered = replace(record, output_write_enabled=True)
    result = _verify(tampered)
    assert result.valid is False


def test_resume_write_enabled_true_fails():
    record = _make_authentic_record()
    tampered = replace(record, resume_write_enabled=True)
    result = _verify(tampered)
    assert result.valid is False


def test_cache_write_enabled_true_fails():
    record = _make_authentic_record()
    tampered = replace(record, cache_write_enabled=True)
    result = _verify(tampered)
    assert result.valid is False


def test_retry_enabled_true_fails():
    record = _make_authentic_record()
    tampered = replace(record, retry_enabled=True)
    result = _verify(tampered)
    assert result.valid is False


def test_fallback_enabled_true_fails():
    record = _make_authentic_record()
    tampered = replace(record, fallback_enabled=True)
    result = _verify(tampered)
    assert result.valid is False


def test_production_hook_enabled_true_fails():
    record = _make_authentic_record()
    tampered = replace(record, production_hook_enabled=True)
    result = _verify(tampered)
    assert result.valid is False


def test_consumption_request_fingerprint_mismatch_fails():
    record = _make_authentic_record()
    result = verify_consumption_record(
        record,
        request_fingerprint=_fake_sha256("wrong-cr"),
        authorization_id=record.authorization_id,
        authorization_request_fingerprint=record.authorization_request_fingerprint,
        authorization_decision_fingerprint=record.authorization_decision_fingerprint,
        execution_plan_fingerprint=record.execution_plan_fingerprint,
        adapter_index=record.selected_adapter_index,
        unit_count=record.consumed_unit_count,
    )
    assert result.valid is False