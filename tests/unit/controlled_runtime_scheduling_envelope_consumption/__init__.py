from core.controlled_runtime_scheduling_envelope import (
    ControlledRuntimeSchedulingEnvelopeBuilder,
)
from core.controlled_runtime_scheduling_envelope_consumption import (
    ControlledRuntimeSchedulingEnvelopeConsumptionRequest,
)
from tests.unit.controlled_runtime_scheduling_envelope import (
    build_context as build_stage68_context,
)


def build_context(tmp_path, **request_overrides):
    stage68_context = build_stage68_context(tmp_path)
    stage68_result = ControlledRuntimeSchedulingEnvelopeBuilder().build(
        **stage68_context
    )
    envelope = stage68_result.scheduling_envelope
    assert envelope is not None
    envelope_request = stage68_context["request"]
    stage67_claim = stage68_context["stage67_scheduling_consumption_claim"]
    stage66_decision = stage68_context["stage66_scheduling_decision"]
    values = dict(
        scheduling_envelope_id=envelope.scheduling_envelope_id,
        scheduling_envelope_fingerprint=envelope.scheduling_envelope_fingerprint,
        scheduling_envelope_request_id=envelope_request.scheduling_envelope_id,
        scheduling_envelope_request_fingerprint=
            envelope_request.request_fingerprint,
        stage67_consumption_claim_id=stage67_claim.scheduling_consumption_id,
        stage67_claim_fingerprint=stage67_claim.claim_fingerprint,
        stage66_scheduling_authorization_id=
            stage66_decision.scheduling_authorization_id,
        stage66_decision_fingerprint=stage66_decision.decision_fingerprint,
        runtime_boundary_id=envelope.runtime_boundary_id,
        runtime_boundary_kind=envelope.runtime_boundary_kind,
        selected_adapter_index=envelope.selected_adapter_index,
        unit_scope=1,
        upstream_fingerprint_chain=envelope.upstream_fingerprint_chain,
    )
    values.update(request_overrides)
    request = ControlledRuntimeSchedulingEnvelopeConsumptionRequest(**values)
    context = dict(stage68_context)
    context.pop("request")
    context.pop("freeze_validation")
    context.pop("authorization_request")
    context.pop("authorization_result")
    context.pop("stage62_request")
    context.pop("stage62_result")
    context.pop("stage63_claim_request")
    context.pop("stage63_result")
    context.pop("stage64_envelope_request")
    context.pop("stage64_result")
    context.pop("stage65_handoff_request")
    context.pop("stage65_result")
    context.pop("stage66_scheduling_request")
    context.pop("stage66_scheduling_result")
    context.update(
        request=request,
        scheduling_envelope=envelope,
        scheduling_envelope_request=envelope_request,
        scheduling_envelope_result=stage68_result,
        database_path=tmp_path / "stage69.sqlite3",
        allowed_root=tmp_path,
    )
    return context
