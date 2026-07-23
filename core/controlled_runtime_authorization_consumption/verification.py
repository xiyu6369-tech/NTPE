"""Stage 6.2 — Consumption Record Verification API

Deterministic offline verification of a consumption record.
never executes, never writes, never contacts network or providers.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .models import (
    CONSUMPTION_RECORD_SCHEMA_NAME,
    CONSUMPTION_RECORD_SCHEMA_VERSION,
    ControlledRuntimeAuthorizationConsumptionRecord,
)

_HEX_64_RE = __import__("re").compile(r"^[a-f0-9]{64}\Z")


# ---------------------------------------------------------------------------
# Verification result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConsumptionRecordVerificationResult:
    valid: bool
    schema_verified: bool
    fingerprint_verified: bool
    request_binding_verified: bool
    authorization_binding_verified: bool
    plan_binding_verified: bool
    adapter_index_verified: bool
    unit_count_verified: bool
    upstream_chain_verified: bool
    previous_consumed_verified: bool
    non_reusable_verified: bool
    no_durable_store_claimed: bool
    no_execution_claimed: bool
    enablement_all_false: bool
    write_indicators_all_false: bool
    reason_codes: tuple[str, ...]
    schema_name_value: str
    schema_version_value: str


# ---------------------------------------------------------------------------
# Verification entry point
# ---------------------------------------------------------------------------


def verify_consumption_record(
    record: ControlledRuntimeAuthorizationConsumptionRecord,
    *,
    request_fingerprint: str,
    authorization_id: str,
    authorization_request_fingerprint: str,
    authorization_decision_fingerprint: str,
    execution_plan_fingerprint: str,
    adapter_index: int,
    unit_count: int = 1,
) -> ConsumptionRecordVerificationResult:
    """Verify an immutable consumption record offline.

    Args:
        record: The consumption record to verify.
        request_fingerprint: The expected consumption request fingerprint.
        authorization_id: The expected authorization ID.
        authorization_request_fingerprint: The expected Stage 6.1 request fingerprint.
        authorization_decision_fingerprint: The expected Stage 6.1 decision fingerprint.
        execution_plan_fingerprint: The expected execution plan fingerprint.
        adapter_index: The expected selected adapter index.
        unit_count: The expected unit count (default 1).

    Returns:
        A frozen ConsumptionRecordVerificationResult.
    """
    reason_codes: list[str] = []

    # Schema
    schema_ok = (
        record.schema_name == CONSUMPTION_RECORD_SCHEMA_NAME
        and record.schema_version == CONSUMPTION_RECORD_SCHEMA_VERSION
    )
    if not schema_ok:
        reason_codes.append("INVALID_SCHEMA")

    # Fingerprint
    fp_raw = {}
    for f in (
        "consumption_id",
        "authorization_id",
        "authorization_request_fingerprint",
        "authorization_decision_fingerprint",
        "execution_plan_fingerprint",
        "selected_adapter_index",
        "consumed_unit_count",
        "previous_authorization_consumed",
        "authorization_consumption_prepared",
        "authorization_consumed",
        "authorization_reusable",
        "durable_reuse_prevention_established",
        "persistent_registry_written",
        "execution_started",
        "execution_completed",
        "runtime_execution_enabled",
        "provider_execution_enabled",
        "network_execution_enabled",
        "translation_execution_enabled",
        "output_write_enabled",
        "resume_write_enabled",
        "cache_write_enabled",
        "retry_enabled",
        "fallback_enabled",
        "production_hook_enabled",
        "status",
        "reason_codes",
        "consumption_request_fingerprint",
        "schema_name",
        "schema_version",
    ):
        fp_raw[f] = getattr(record, f)
    expected_fp = hashlib.sha256(
        json.dumps(fp_raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()
    fp_ok = record.record_fingerprint == expected_fp
    if not fp_ok:
        reason_codes.append("RECORD_FINGERPRINT_MISMATCH")

    # Request binding
    req_ok = record.consumption_request_fingerprint == request_fingerprint
    if not req_ok:
        reason_codes.append("REQUEST_FINGERPRINT_MISMATCH")

    # Authorization ID binding
    auth_id_ok = record.authorization_id == authorization_id
    if not auth_id_ok:
        reason_codes.append("AUTHORIZATION_ID_MISMATCH")

    # Authorization request binding
    auth_req_ok = record.authorization_request_fingerprint == authorization_request_fingerprint
    if not auth_req_ok:
        reason_codes.append("AUTH_REQUEST_FINGERPRINT_MISMATCH")

    # Authorization decision binding
    auth_dec_ok = record.authorization_decision_fingerprint == authorization_decision_fingerprint
    if not auth_dec_ok:
        reason_codes.append("AUTH_DECISION_FINGERPRINT_MISMATCH")

    # Execution plan binding
    plan_ok = record.execution_plan_fingerprint == execution_plan_fingerprint
    if not plan_ok:
        reason_codes.append("EXECUTION_PLAN_FINGERPRINT_MISMATCH")

    # Adapter index binding
    adapter_ok = record.selected_adapter_index == adapter_index
    if not adapter_ok:
        reason_codes.append("ADAPTER_INDEX_MISMATCH")

    # Unit count binding
    unit_ok = record.consumed_unit_count == unit_count
    if not unit_ok:
        reason_codes.append("UNIT_COUNT_MISMATCH")

    # Upstream fingerprint chain (must be 11 elements, last one = record fingerprint)
    chain_ok = len(record.upstream_fingerprint_chain) == 11 and record.upstream_fingerprint_chain[10] == record.record_fingerprint
    if not chain_ok:
        reason_codes.append("UPSTREAM_CHAIN_MISMATCH")

    # Previous consumed must be false
    prior_ok = not record.previous_authorization_consumed
    if not prior_ok:
        reason_codes.append("PREVIOUS_CONSUMED_TRUE")

    # Non-reusable
    non_reuse_ok = not record.authorization_reusable
    if not non_reuse_ok:
        reason_codes.append("AUTHORIZATION_REUSABLE")

    # No durable store claim
    no_store_ok = not record.persistent_registry_written and not record.durable_reuse_prevention_established
    if not no_store_ok:
        reason_codes.append("DURABLE_STORE_CLAIMED")

    # No execution claim
    no_exec_ok = not record.execution_started and not record.execution_completed
    if not no_exec_ok:
        reason_codes.append("EXECUTION_CLAIMED")

    # All enablement false
    enable_ok = all(
        not getattr(record, f)
        for f in (
            "runtime_execution_enabled",
            "provider_execution_enabled",
            "network_execution_enabled",
            "translation_execution_enabled",
        )
    )
    if not enable_ok:
        reason_codes.append("ENABLEMENT_TRUE")

    # All write indicators false
    write_ok = all(
        not getattr(record, f)
        for f in (
            "output_write_enabled",
            "resume_write_enabled",
            "cache_write_enabled",
            "retry_enabled",
            "fallback_enabled",
            "production_hook_enabled",
        )
    )
    if not write_ok:
        reason_codes.append("WRITE_INDICATOR_TRUE")

    valid = all(
        [
            schema_ok,
            fp_ok,
            req_ok,
            auth_id_ok,
            auth_req_ok,
            auth_dec_ok,
            plan_ok,
            adapter_ok,
            unit_ok,
            chain_ok,
            prior_ok,
            non_reuse_ok,
            no_store_ok,
            no_exec_ok,
            enable_ok,
            write_ok,
        ]
    )

    return ConsumptionRecordVerificationResult(
        valid=valid,
        schema_verified=schema_ok,
        fingerprint_verified=fp_ok,
        request_binding_verified=req_ok,
        authorization_binding_verified=(auth_id_ok and auth_req_ok and auth_dec_ok),
        plan_binding_verified=(plan_ok and adapter_ok and unit_ok),
        adapter_index_verified=adapter_ok,
        unit_count_verified=unit_ok,
        upstream_chain_verified=chain_ok,
        previous_consumed_verified=prior_ok,
        non_reusable_verified=non_reuse_ok,
        no_durable_store_claimed=no_store_ok,
        no_execution_claimed=no_exec_ok,
        enablement_all_false=enable_ok,
        write_indicators_all_false=write_ok,
        reason_codes=tuple(reason_codes),
        schema_name_value=record.schema_name,
        schema_version_value=record.schema_version,
    )