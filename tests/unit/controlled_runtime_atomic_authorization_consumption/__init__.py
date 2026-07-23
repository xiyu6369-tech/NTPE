"""Shared authentic contract builder for Stage 6.3 tests."""

from dataclasses import fields, replace

from core.controlled_runtime_authorization_consumption import (
    ControlledRuntimeAuthorizationConsumer,
    ControlledRuntimeAuthorizationConsumptionRequest,
)
from core.controlled_runtime_authorization_consumption.policy import exact_consumption_scope
from core.controlled_runtime_atomic_authorization_consumption import (
    AtomicAuthorizationConsumptionClaimRequest,
    AtomicAuthorizationConsumptionRegistry,
)
from core.controlled_runtime_atomic_authorization_consumption.models import canonical_sha256
from tests.unit.controlled_runtime_authorization_consumption.test_consumer import (
    _make_setup,
)


def build_context(tmp_path, *, claim_id="stage-6.3-claim-001"):
    plan, auth_request, auth_decision, freeze_metadata, _ = _make_setup()
    decision_payload = {
        item.name: getattr(auth_decision, item.name)
        for item in fields(auth_decision) if item.name != "decision_fingerprint"
    }
    decision_payload["reason_codes"] = list(decision_payload["reason_codes"])
    auth_decision = replace(
        auth_decision, decision_fingerprint=canonical_sha256(decision_payload),
    )
    stage62_consumer = ControlledRuntimeAuthorizationConsumer()
    stage62_request = ControlledRuntimeAuthorizationConsumptionRequest(
        consumption_id="stage-6.3-consumption-001",
        authorization_id=auth_decision.authorization_id,
        authorization_request_fingerprint=auth_request.request_fingerprint,
        authorization_decision_fingerprint=auth_decision.decision_fingerprint,
        execution_plan_fingerprint=plan.execution_plan_fingerprint,
        selected_adapter_index=0,
        requested_unit_count=1,
        consume_for_single_execution=True,
        caller_confirmation=True,
        consumption_scope=exact_consumption_scope(
            auth_decision.authorization_id, auth_request.request_fingerprint,
            auth_decision.decision_fingerprint, plan.execution_plan_fingerprint, 0, 1,
        ),
        purpose="stage-6.3-authentic-preparation",
        schema_name="ntpe.controlled_runtime_authorization_consumption_request",
        schema_version="1.0",
    )
    stage62_result = stage62_consumer.prepare_consumption(
        request=stage62_request, authorization_request=auth_request,
        authorization_decision=auth_decision, execution_plan=plan,
        freeze_metadata=freeze_metadata,
    )
    registry = AtomicAuthorizationConsumptionRegistry(tmp_path / "claims.sqlite3", tmp_path)
    request = AtomicAuthorizationConsumptionClaimRequest(
        claim_id=claim_id, consumption_id=stage62_request.consumption_id,
        authorization_id=auth_decision.authorization_id,
        authorization_request_fingerprint=auth_request.request_fingerprint,
        authorization_decision_fingerprint=auth_decision.decision_fingerprint,
        execution_plan_fingerprint=plan.execution_plan_fingerprint,
        stage62_request_fingerprint=stage62_request.request_fingerprint,
        stage62_record_fingerprint=stage62_result.record.record_fingerprint,
        selected_adapter_index=0, requested_unit_count=1,
        claim_for_single_execution=True, caller_confirmation=True,
        registry_scope=registry.registry_scope, purpose="durably claim only",
    )
    return {
        "request": request, "execution_plan": plan, "freeze_metadata": freeze_metadata,
        "authorization_request": auth_request, "authorization_decision": auth_decision,
        "stage62_request": stage62_request, "stage62_record": stage62_result.record,
        "stage62_result": stage62_result, "registry": registry,
    }
