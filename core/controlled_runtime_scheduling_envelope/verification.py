"""Pure offline verification for Stage 6.8 scheduling envelopes."""

from __future__ import annotations

from .errors import ControlledRuntimeSchedulingEnvelopeVerificationError
from .models import (
    ENVELOPE_SCHEMA_NAME,
    ENVELOPE_SCHEMA_VERSION,
    ControlledRuntimeSchedulingEnvelope,
    ControlledRuntimeSchedulingEnvelopeRequest,
    _ControlledRuntimeSchedulingEnvelopeVerificationResult,
    canonical_sha256,
)
from .policy import BOUNDARY_KIND, DEFAULT_POLICY, SUCCESS_STATUS


def verify_controlled_runtime_scheduling_envelope(
    scheduling_envelope: ControlledRuntimeSchedulingEnvelope,
    *,
    request: ControlledRuntimeSchedulingEnvelopeRequest | None = None,
    stage67_scheduling_consumption_request: object | None = None,
    stage67_scheduling_consumption_claim: object | None = None,
    stage66_scheduling_decision: object | None = None,
    stage65_handoff_receipt: object | None = None,
    stage64_envelope: object | None = None,
    stage63_claim: object | None = None,
    stage62_record: object | None = None,
    authorization_decision: object | None = None,
    execution_plan: object | None = None,
    raise_on_error: bool = False,
) -> _ControlledRuntimeSchedulingEnvelopeVerificationResult:
    if not isinstance(
        scheduling_envelope,
        ControlledRuntimeSchedulingEnvelope,
    ):
        raise TypeError("scheduling_envelope must be a Stage 6.8 envelope")

    envelope = scheduling_envelope
    chain = tuple(envelope.upstream_fingerprint_chain)
    schema_ok = (
        envelope.schema_name == ENVELOPE_SCHEMA_NAME
        and envelope.schema_version == ENVELOPE_SCHEMA_VERSION
    )
    fingerprint_ok = (
        envelope.scheduling_envelope_fingerprint
        == canonical_sha256(envelope._fingerprint_payload(chain[:22]))
    )
    chain_ok = all(
        (
            len(chain) == DEFAULT_POLICY.complete_chain_layers,
            chain[6] == envelope.execution_plan_fingerprint,
            chain[8] == envelope.execution_authorization_decision_fingerprint,
            chain[12] == envelope.stage63_claim_fingerprint,
            chain[14] == envelope.stage64_envelope_fingerprint,
            chain[16] == envelope.stage65_handoff_receipt_fingerprint,
            chain[17] == envelope.stage66_scheduling_request_fingerprint,
            chain[18] == envelope.stage66_scheduling_decision_fingerprint,
            chain[19]
            == envelope.stage67_scheduling_consumption_request_fingerprint,
            chain[20]
            == envelope.stage67_scheduling_consumption_claim_fingerprint,
            chain[21] == envelope.scheduling_envelope_request_fingerprint,
            chain[22] == envelope.scheduling_envelope_fingerprint,
        )
    )
    request_ok = (
        request is None
        or all(
            (
                request.request_fingerprint
                == canonical_sha256(request._fingerprint_payload()),
                envelope.scheduling_envelope_request_fingerprint
                == request.request_fingerprint,
                envelope.scheduling_envelope_id == request.scheduling_envelope_id,
                envelope.scheduling_consumption_id
                == request.scheduling_consumption_id,
                envelope.scheduling_authorization_id
                == request.scheduling_authorization_id,
                envelope.handoff_id == request.handoff_id,
                envelope.envelope_id == request.envelope_id,
                envelope.claim_id == request.claim_id,
                envelope.consumption_id == request.consumption_id,
                envelope.authorization_id == request.authorization_id,
                envelope.selected_adapter_index
                == request.selected_adapter_index,
                envelope.runtime_boundary_id == request.runtime_boundary_id,
                envelope.runtime_boundary_kind == request.runtime_boundary_kind,
            )
        )
    )
    stage67_ok = all(
        (
            stage67_scheduling_consumption_request is None
            or all(
                (
                    envelope.scheduling_consumption_id
                    == getattr(
                        stage67_scheduling_consumption_request,
                        "scheduling_consumption_id",
                        None,
                    ),
                    envelope.stage67_scheduling_consumption_request_fingerprint
                    == getattr(
                        stage67_scheduling_consumption_request,
                        "request_fingerprint",
                        None,
                    ),
                )
            ),
            stage67_scheduling_consumption_claim is None
            or all(
                (
                    envelope.stage67_scheduling_consumption_claim_fingerprint
                    == getattr(
                        stage67_scheduling_consumption_claim,
                        "claim_fingerprint",
                        None,
                    ),
                    tuple(
                        getattr(
                            stage67_scheduling_consumption_claim,
                            "upstream_fingerprint_chain",
                            (),
                        )
                    )
                    == chain[:21],
                )
            ),
        )
    )
    stage66_ok = (
        stage66_scheduling_decision is None
        or all(
            (
                envelope.scheduling_authorization_id
                == getattr(
                    stage66_scheduling_decision,
                    "scheduling_authorization_id",
                    None,
                ),
                envelope.stage66_scheduling_decision_fingerprint
                == getattr(
                    stage66_scheduling_decision,
                    "decision_fingerprint",
                    None,
                ),
            )
        )
    )
    stage65_ok = (
        stage65_handoff_receipt is None
        or all(
            (
                envelope.handoff_id
                == getattr(stage65_handoff_receipt, "handoff_id", None),
                envelope.stage65_handoff_receipt_fingerprint
                == getattr(
                    stage65_handoff_receipt,
                    "receipt_fingerprint",
                    None,
                ),
            )
        )
    )
    stage64_ok = (
        stage64_envelope is None
        or all(
            (
                envelope.envelope_id
                == getattr(stage64_envelope, "envelope_id", None),
                envelope.stage64_envelope_fingerprint
                == getattr(stage64_envelope, "envelope_fingerprint", None),
            )
        )
    )
    stage63_ok = (
        stage63_claim is None
        or all(
            (
                envelope.claim_id == getattr(stage63_claim, "claim_id", None),
                envelope.stage63_claim_fingerprint
                == getattr(stage63_claim, "claim_fingerprint", None),
            )
        )
    )
    stage62_ok = (
        stage62_record is None
        or envelope.consumption_id
        == getattr(stage62_record, "consumption_id", None)
    )
    stage61_ok = (
        authorization_decision is None
        or all(
            (
                envelope.authorization_id
                == getattr(authorization_decision, "authorization_id", None),
                envelope.execution_authorization_decision_fingerprint
                == getattr(authorization_decision, "decision_fingerprint", None),
            )
        )
    )
    plan_ok = (
        execution_plan is None
        or envelope.execution_plan_fingerprint
        == getattr(execution_plan, "execution_plan_fingerprint", None)
    )
    adapter_values = [envelope.selected_adapter_index]
    for upstream in (
        request,
        stage67_scheduling_consumption_request,
        stage67_scheduling_consumption_claim,
        stage66_scheduling_decision,
        stage65_handoff_receipt,
        stage64_envelope,
        stage63_claim,
    ):
        if upstream is not None:
            adapter_values.append(
                getattr(upstream, "selected_adapter_index", None)
            )
    adapter_ok = (
        type(envelope.selected_adapter_index) is int
        and all(
            value == envelope.selected_adapter_index
            for value in adapter_values
        )
    )
    unit_ok = (
        type(envelope.schedule_unit_count) is int
        and envelope.schedule_unit_count == 1
        and (
            request is None
            or request.requested_schedule_unit_count == 1
        )
    )
    boundary_ok = all(
        (
            isinstance(envelope.runtime_boundary_id, str),
            bool(envelope.runtime_boundary_id),
            envelope.runtime_boundary_kind == BOUNDARY_KIND,
            stage67_scheduling_consumption_claim is None
            or envelope.runtime_boundary_id
            == getattr(
                stage67_scheduling_consumption_claim,
                "runtime_boundary_id",
                None,
            ),
        )
    )
    state_ok = all(
        (
            envelope.authorization_consumed,
            not envelope.authorization_reusable,
            envelope.durable_reuse_prevention_established,
            envelope.persistent_registry_written,
            envelope.runtime_handoff_prepared,
            envelope.runtime_handoff_completed,
            envelope.runtime_boundary_accepted,
            envelope.scheduling_authorization_requested,
            envelope.scheduling_authorized,
            envelope.scheduling_authorization_consumed,
            not envelope.scheduling_authorization_reusable,
            envelope.schedule_once,
            envelope.durable_scheduling_reuse_prevention_established,
            envelope.persistent_scheduling_registry_written,
            envelope.scheduling_envelope_prepared,
            not envelope.scheduling_envelope_consumed,
            not envelope.scheduling_envelope_reusable,
            not envelope.queue_admission_authorized,
            not envelope.runtime_execution_scheduled,
            not envelope.queue_record_created,
            not envelope.job_record_created,
            not envelope.worker_started,
            not envelope.execution_started,
            not envelope.execution_completed,
            envelope.envelope_state == SUCCESS_STATUS,
        )
    )
    disabled_ok = not any(
        getattr(envelope, name)
        for name in (
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
        )
    )
    checks = (
        ("INVALID_SCHEMA", schema_ok),
        ("ENVELOPE_FINGERPRINT_MISMATCH", fingerprint_ok),
        ("REQUEST_BINDING_MISMATCH", request_ok),
        ("STAGE67_BINDING_MISMATCH", stage67_ok),
        ("STAGE66_BINDING_MISMATCH", stage66_ok),
        ("STAGE65_BINDING_MISMATCH", stage65_ok),
        ("STAGE64_BINDING_MISMATCH", stage64_ok),
        ("STAGE63_BINDING_MISMATCH", stage63_ok),
        ("STAGE62_BINDING_MISMATCH", stage62_ok),
        ("STAGE61_BINDING_MISMATCH", stage61_ok),
        ("PLAN_BINDING_MISMATCH", plan_ok),
        ("ADAPTER_INDEX_MISMATCH", adapter_ok),
        ("UNIT_COUNT_MISMATCH", unit_ok),
        ("RUNTIME_BOUNDARY_MISMATCH", boundary_ok),
        ("UPSTREAM_CHAIN_MISMATCH", chain_ok),
        ("ENVELOPE_STATE_INVALID", state_ok),
        ("CAPABILITY_ENABLED", disabled_ok),
    )
    reasons = tuple(code for code, valid in checks if not valid)
    result = _ControlledRuntimeSchedulingEnvelopeVerificationResult(
        valid=not reasons,
        schema_verified=schema_ok,
        fingerprint_verified=fingerprint_ok,
        request_binding_verified=request_ok,
        stage67_binding_verified=stage67_ok,
        stage66_binding_verified=stage66_ok,
        stage65_binding_verified=stage65_ok,
        stage64_binding_verified=stage64_ok,
        stage63_binding_verified=stage63_ok,
        stage62_binding_verified=stage62_ok,
        stage61_binding_verified=stage61_ok,
        plan_binding_verified=plan_ok,
        adapter_index_verified=adapter_ok,
        unit_count_verified=unit_ok,
        runtime_boundary_verified=boundary_ok,
        upstream_chain_verified=chain_ok,
        state_verified=state_ok,
        capabilities_disabled=disabled_ok,
        reason_codes=reasons,
    )
    if raise_on_error and not result.valid:
        raise ControlledRuntimeSchedulingEnvelopeVerificationError(
            ",".join(result.reason_codes)
        )
    return result
