from __future__ import annotations

from dataclasses import replace
from typing import Callable

from core.controlled_runtime_execution_plan import (
    ControlledRuntimeExecutionPlan,
    ControlledRuntimePreparationFreezeMetadata,
    ControlledRuntimePreparationFreezeValidationResult,
    get_controlled_runtime_preparation_freeze_metadata,
    validate_controlled_runtime_preparation_freeze,
)
from core.controlled_runtime_execution_authorization import (
    ControlledRuntimeExecutionAuthorizationDecision,
    ControlledRuntimeExecutionAuthorizationRequest,
)
from .models import (
    CONSUMPTION_RECORD_SCHEMA_NAME,
    CONSUMPTION_RECORD_SCHEMA_VERSION,
    ControlledRuntimeAuthorizationConsumptionFinding,
    ControlledRuntimeAuthorizationConsumptionRecord,
    ControlledRuntimeAuthorizationConsumptionRequest,
    ControlledRuntimeAuthorizationConsumptionResult,
)
from .policy import exact_consumption_scope


# ---------------------------------------------------------------------------
# Finding codes (Stage 6.2 canonical) — deterministic messages
# ---------------------------------------------------------------------------

_FINDING_CODES = {
    "EMPTY_CONSUMPTION_ID": "consumption_id is empty or blank",
    "MALFORMED_CONSUMPTION_ID": "consumption_id is structurally invalid",
    "CONFIRMATION_FALSE": "caller_confirmation must be true",
    "CONFIRMATION_MALFORMED": "caller_confirmation must be bool true",
    "SINGLE_EXECUTION_FALSE": "consume_for_single_execution must be exactly true",
    "MALFORMED_SINGLE_EXECUTION": "consume_for_single_execution must be bool true",
    "AUTHORIZATION_ID_MISMATCH": "authorization_id does not match the authorization decision",
    "AUTH_REQ_FINGERPRINT_MISMATCH": "authorization_request_fingerprint does not match the supplied authorization request",
    "AUTH_DEC_FINGERPRINT_MISMATCH": "authorization_decision_fingerprint does not match the supplied authorization decision",
    "PLAN_FINGERPRINT_MISMATCH": "execution_plan_fingerprint does not match the supplied execution plan",
    "ADAPTER_INDEX_MISMATCH": "selected_adapter_index does not match the execution plan's selected index",
    "UNIT_COUNT_ZERO": "requested_unit_count must be exactly 1, got 0",
    "UNIT_COUNT_GT_ONE": "requested_unit_count must be exactly 1",
    "UNIT_COUNT_BOOL": "requested_unit_count must be int, got bool",
    "SCOPE_BROADER": "consumption_scope does not exactly bind to all required elements",
    "INVALID_REQUEST_SCHEMA": "schema_name or schema_version invalid",
    "INVALID_REQUEST_VERSION": "schema_version not 1.0",
    "INVALID_REQUEST_FINGERPRINT": "request_fingerprint does not match canonical payload",
    "FINGERPRINT_TAMPERED": "a tampered fingerprint was detected",
    # Upstream
    "FREEZE_GATE_FAILED": "Stage 5.4 freeze validation failed",
    "FREEZE_METADATA_MISSING": "freeze metadata is None",
    "FREEZE_DRIFT": "freeze metadata does not match the canonical Stage 5.4 contract",
    "PLAN_INVALID": "execution plan fails canonical Stage 5.3 verification",
    "PLAN_TAMPERED": "execution plan fingerprint mismatch",
    "PLAN_MULTIPLE_SELECTED": "execution plan has more than one selected unit",
    "PLAN_AUTO_SELECTION": "execution plan used automatic unit selection",
    "PLAN_STARTED": "execution plan already started",
    "PLAN_COMPLETED": "execution plan already completed",
    "PLAN_WRONG_STATUS": "execution plan status is not planned_not_executed",
    "PROVIDER_COUNTER_NONZERO": "provider execution counter is not zero",
    "TRANSLATION_COUNTER_NONZERO": "translation execution counter is not zero",
    # Stage 6.1
    "AUTH_REQ_INVALID": "Stage 6.1 authorization request fails canonical verification",
    "AUTH_DEC_INVALID": "Stage 6.1 authorization decision fails canonical verification",
    "AUTH_REJECTED": "authorization authorized is false",
    "AUTH_WRONG_STATUS": "authorization status is not authorized_not_executed",
    "AUTH_ALREADY_CONSUMED": "authorization already consumed",
    "AUTH_REUSABLE": "authorization marked reusable",
    "PROVIDER_LIMIT_WRONG": "authorized provider request limit is not exactly 1",
    "TRANSLATION_LIMIT_WRONG": "authorized translation request limit is not exactly 1",
    "RETRY_LIMIT_NONZERO": "authorized retry limit is greater than 0",
    "FALLBACK_LIMIT_NONZERO": "authorized fallback limit is greater than 0",
    "OUTPUT_REPLACEMENT_AUTHORIZED": "output replacement authorized is true",
    "OUTPUT_REPLACEMENT_AUTHORIZED_PLAN": "output replacement authorized on plan is true",
    "PRODUCTION_INTEGRATION_AUTHORIZED": "production integration authorized is true",
    # Enablement
    "RUNTIME_ENABLEMENT_TRUE": "runtime_execution_enabled is true",
    "PROVIDER_ENABLEMENT_TRUE": "provider_execution_enabled is true",
    "NETWORK_ENABLEMENT_TRUE": "network_execution_enabled is true",
    "TRANSLATION_ENABLEMENT_TRUE": "translation_execution_enabled is true",
    "CACHE_WRITE_REQUESTED": "cache write requested or implied",
    "RESUME_WRITE_REQUESTED": "resume write requested or implied",
    "OUTPUT_WRITE_REQUESTED": "output write requested or implied",
    "RETRY_REQUESTED": "retry requested or implied",
    "FALLBACK_REQUESTED": "fallback requested or implied",
    "PRODUCTION_HOOK_REQUESTED": "production hook requested or implied",
    "REGISTRY_FALSELY_CLAIMED": "persistent registry falsely claimed",
    "DURABLE_FALSELY_CLAIMED": "durable reuse prevention falsely claimed",
}

_FINDING_SEVERITIES: dict[str, str] = {
    "EMPTY_CONSUMPTION_ID": "blocking",
    "MALFORMED_CONSUMPTION_ID": "blocking",
    "CONFIRMATION_FALSE": "blocking",
    "CONFIRMATION_MALFORMED": "blocking",
    "SINGLE_EXECUTION_FALSE": "blocking",
    "MALFORMED_SINGLE_EXECUTION": "blocking",
    "AUTHORIZATION_ID_MISMATCH": "blocking",
    "AUTH_REQ_FINGERPRINT_MISMATCH": "blocking",
    "AUTH_DEC_FINGERPRINT_MISMATCH": "blocking",
    "PLAN_FINGERPRINT_MISMATCH": "blocking",
    "ADAPTER_INDEX_MISMATCH": "blocking",
    "UNIT_COUNT_ZERO": "blocking",
    "UNIT_COUNT_GT_ONE": "blocking",
    "UNIT_COUNT_BOOL": "blocking",
    "SCOPE_BROADER": "blocking",
    "INVALID_REQUEST_SCHEMA": "blocking",
    "INVALID_REQUEST_VERSION": "blocking",
    "INVALID_REQUEST_FINGERPRINT": "blocking",
    "FINGERPRINT_TAMPERED": "blocking",
    "FREEZE_GATE_FAILED": "blocking",
    "FREEZE_METADATA_MISSING": "blocking",
    "FREEZE_DRIFT": "blocking",
    "PLAN_INVALID": "blocking",
    "PLAN_TAMPERED": "blocking",
    "PLAN_MULTIPLE_SELECTED": "blocking",
    "PLAN_AUTO_SELECTION": "blocking",
    "PLAN_STARTED": "blocking",
    "PLAN_COMPLETED": "blocking",
    "PLAN_WRONG_STATUS": "blocking",
    "PROVIDER_COUNTER_NONZERO": "blocking",
    "TRANSLATION_COUNTER_NONZERO": "blocking",
    "AUTH_REQ_INVALID": "blocking",
    "AUTH_DEC_INVALID": "blocking",
    "AUTH_REJECTED": "blocking",
    "AUTH_WRONG_STATUS": "blocking",
    "AUTH_ALREADY_CONSUMED": "blocking",
    "AUTH_REUSABLE": "blocking",
    "PROVIDER_LIMIT_WRONG": "blocking",
    "TRANSLATION_LIMIT_WRONG": "blocking",
    "RETRY_LIMIT_NONZERO": "blocking",
    "FALLBACK_LIMIT_NONZERO": "blocking",
    "OUTPUT_REPLACEMENT_AUTHORIZED": "blocking",
    "OUTPUT_REPLACEMENT_AUTHORIZED_PLAN": "blocking",
    "PRODUCTION_INTEGRATION_AUTHORIZED": "blocking",
    "RUNTIME_ENABLEMENT_TRUE": "blocking",
    "PROVIDER_ENABLEMENT_TRUE": "blocking",
    "NETWORK_ENABLEMENT_TRUE": "blocking",
    "TRANSLATION_ENABLEMENT_TRUE": "blocking",
    "CACHE_WRITE_REQUESTED": "blocking",
    "RESUME_WRITE_REQUESTED": "blocking",
    "OUTPUT_WRITE_REQUESTED": "blocking",
    "RETRY_REQUESTED": "blocking",
    "FALLBACK_REQUESTED": "blocking",
    "PRODUCTION_HOOK_REQUESTED": "blocking",
    "REGISTRY_FALSELY_CLAIMED": "blocking",
    "DURABLE_FALSELY_CLAIMED": "blocking",
}

# Ordering for determinism
_FINDING_ORDER: tuple[str, ...] = (
    "EMPTY_CONSUMPTION_ID",
    "MALFORMED_CONSUMPTION_ID",
    "CONFIRMATION_FALSE",
    "CONFIRMATION_MALFORMED",
    "SINGLE_EXECUTION_FALSE",
    "MALFORMED_SINGLE_EXECUTION",
    "AUTHORIZATION_ID_MISMATCH",
    "AUTH_REQ_FINGERPRINT_MISMATCH",
    "AUTH_DEC_FINGERPRINT_MISMATCH",
    "PLAN_FINGERPRINT_MISMATCH",
    "ADAPTER_INDEX_MISMATCH",
    "UNIT_COUNT_ZERO",
    "UNIT_COUNT_GT_ONE",
    "UNIT_COUNT_BOOL",
    "SCOPE_BROADER",
    "INVALID_REQUEST_SCHEMA",
    "INVALID_REQUEST_VERSION",
    "INVALID_REQUEST_FINGERPRINT",
    "FINGERPRINT_TAMPERED",
    "FREEZE_GATE_FAILED",
    "FREEZE_METADATA_MISSING",
    "FREEZE_DRIFT",
    "PLAN_INVALID",
    "PLAN_TAMPERED",
    "PLAN_MULTIPLE_SELECTED",
    "PLAN_AUTO_SELECTION",
    "PLAN_STARTED",
    "PLAN_COMPLETED",
    "PLAN_WRONG_STATUS",
    "PROVIDER_COUNTER_NONZERO",
    "TRANSLATION_COUNTER_NONZERO",
    "AUTH_REQ_INVALID",
    "AUTH_DEC_INVALID",
    "AUTH_REJECTED",
    "AUTH_WRONG_STATUS",
    "AUTH_ALREADY_CONSUMED",
    "AUTH_REUSABLE",
    "PROVIDER_LIMIT_WRONG",
    "TRANSLATION_LIMIT_WRONG",
    "RETRY_LIMIT_NONZERO",
    "FALLBACK_LIMIT_NONZERO",
    "OUTPUT_REPLACEMENT_AUTHORIZED",
    "OUTPUT_REPLACEMENT_AUTHORIZED_PLAN",
    "PRODUCTION_INTEGRATION_AUTHORIZED",
    "RUNTIME_ENABLEMENT_TRUE",
    "PROVIDER_ENABLEMENT_TRUE",
    "NETWORK_ENABLEMENT_TRUE",
    "TRANSLATION_ENABLEMENT_TRUE",
    "CACHE_WRITE_REQUESTED",
    "RESUME_WRITE_REQUESTED",
    "OUTPUT_WRITE_REQUESTED",
    "RETRY_REQUESTED",
    "FALLBACK_REQUESTED",
    "PRODUCTION_HOOK_REQUESTED",
    "REGISTRY_FALSELY_CLAIMED",
    "DURABLE_FALSELY_CLAIMED",
)


class _FindingCollector:
    """Deterministic collector — ref-free, no mutable shared state leakage."""

    def __init__(self) -> None:
        self._items: dict[str, ControlledRuntimeAuthorizationConsumptionFinding] = {}

    def add(
        self,
        code: str,
        *,
        field: str = "",
        expected: str = "",
        observed: str = "",
    ) -> None:
        if code not in self._items:
            self._items[code] = ControlledRuntimeAuthorizationConsumptionFinding(
                code=code,
                severity=_FINDING_SEVERITIES[code],
                message=_FINDING_CODES[code],
                field=field,
                expected=expected,
                observed=observed,
            )

    def ordered(self) -> tuple[ControlledRuntimeAuthorizationConsumptionFinding, ...]:
        return tuple(
            sorted(self._items.values(), key=lambda item: _FINDING_ORDER.index(item.code))
        )

    def has_blocking_or_error(self) -> bool:
        for item in self._items.values():
            if item.severity in ("blocking", "error"):
                return True
        return False


# ---------------------------------------------------------------------------
# Consumer
# ---------------------------------------------------------------------------


class ControlledRuntimeAuthorizationConsumer:
    """Prepare one single-use consumption contract for an authorized execution plan.

    Stage 6.2 is offline only — no execution, no writes, no providers, no network.
    """

    def __init__(
        self,
        *,
        freeze_validator: (
            Callable[[], ControlledRuntimePreparationFreezeValidationResult] | None
        ) = None,
        freeze_metadata_provider: (
            Callable[[], ControlledRuntimePreparationFreezeMetadata] | None
        ) = None,
    ) -> None:
        self._freeze_validator = (
            validate_controlled_runtime_preparation_freeze
            if freeze_validator is None
            else freeze_validator
        )
        self._freeze_metadata_provider = (
            get_controlled_runtime_preparation_freeze_metadata
            if freeze_metadata_provider is None
            else freeze_metadata_provider
        )

    def prepare_consumption(
        self,
        *,
        request: ControlledRuntimeAuthorizationConsumptionRequest,
        authorization_request: ControlledRuntimeExecutionAuthorizationRequest,
        authorization_decision: ControlledRuntimeExecutionAuthorizationDecision,
        execution_plan: ControlledRuntimeExecutionPlan,
        freeze_metadata: ControlledRuntimePreparationFreezeMetadata | None,
    ) -> ControlledRuntimeAuthorizationConsumptionResult:
        """Prepare an immutable consumption contract.

        Returns a ControlledRuntimeAuthorizationConsumptionResult.
        Never executes, never writes, never contacts providers or network.
        """
        findings = _FindingCollector()

        # -------------------------------------------------------------------
        # 1. Freeze gate (Stage 5.4)
        # -------------------------------------------------------------------
        freeze_gate_verified = self._verify_freeze_gate(findings)
        freeze_metadata_ok = self._verify_freeze_metadata(freeze_metadata, findings)

        # -------------------------------------------------------------------
        # 2. Execution plan verification (Stage 5.3)
        # -------------------------------------------------------------------
        plan_ok = self._verify_execution_plan(execution_plan, request, findings)

        # -------------------------------------------------------------------
        # 3. Authorization request / decision verification (Stage 6.1)
        # -------------------------------------------------------------------
        auth_req_ok = self._verify_authorization_request(
            authorization_request, request, findings
        )
        auth_dec_ok = self._verify_authorization_decision(
            authorization_decision, request, findings
        )
        auth_bind_ok = self._verify_authorization_binding(
            authorization_request, authorization_decision, execution_plan, request, findings
        )
        prior_ok = self._verify_prior_consumption(authorization_decision, findings)

        # -------------------------------------------------------------------
        # 4. Consumption request validation
        # -------------------------------------------------------------------
        req_ok = self._verify_consumption_request(
            request, authorization_decision, execution_plan, findings
        )

        # -------------------------------------------------------------------
        # 5. Enablement checks
        # -------------------------------------------------------------------
        enable_ok = self._verify_enablement(authorization_decision, execution_plan, findings)

        # -------------------------------------------------------------------
        # Determine status
        # -------------------------------------------------------------------
        all_ok = (
            freeze_gate_verified
            and freeze_metadata_ok
            and plan_ok
            and auth_req_ok
            and auth_dec_ok
            and auth_bind_ok
            and prior_ok
            and req_ok
            and enable_ok
        )

        if findings.has_blocking_or_error():
            status = "rejected"
            recommended_action = "correct_request"
        elif all_ok:
            status = "consumption_prepared_not_executed"
            recommended_action = "retain_for_atomic_execution_boundary"
        else:
            status = "invalid_request"
            recommended_action = "correct_request"

        # -------------------------------------------------------------------
        # Build consumption record
        # -------------------------------------------------------------------
        policy_findings_tuple = findings.ordered()

        upstream_chain = (
            execution_plan.source.execution_package_fingerprint,
            authorization_decision.upstream_authorization_decision_fingerprint,
            execution_plan.source.approval_record_fingerprint,
            execution_plan.source.runtime_submission_package_fingerprint,
            execution_plan.source.runtime_adapter_request_fingerprint,
            execution_plan.source.runtime_adapter_preparation_fingerprint,
            execution_plan.execution_plan_fingerprint,
            authorization_request.request_fingerprint,
            authorization_decision.decision_fingerprint,
            request.request_fingerprint,
            "",  # record fingerprint placeholder — filled below
        )

        record = ControlledRuntimeAuthorizationConsumptionRecord(
            consumption_id=request.consumption_id,
            authorization_id=authorization_decision.authorization_id,
            authorization_request_fingerprint=request.authorization_request_fingerprint,
            authorization_decision_fingerprint=request.authorization_decision_fingerprint,
            execution_plan_fingerprint=request.execution_plan_fingerprint,
            selected_adapter_index=request.selected_adapter_index,
            consumed_unit_count=1,
            previous_authorization_consumed=False,
            authorization_consumption_prepared=all_ok and status == "consumption_prepared_not_executed",
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
            status=status,
            reason_codes=tuple(
                item.code for item in policy_findings_tuple if item.severity in ("error", "blocking")
            ),
            upstream_fingerprint_chain=upstream_chain,
            consumption_request_fingerprint=request.request_fingerprint,
            schema_name=CONSUMPTION_RECORD_SCHEMA_NAME,
            schema_version=CONSUMPTION_RECORD_SCHEMA_VERSION,
        )

        # Patch the record's fingerprint into the upstream chain (position 10)
        chain = list(upstream_chain)
        chain[10] = record.record_fingerprint
        record = replace(record, upstream_fingerprint_chain=tuple(chain))

        # -------------------------------------------------------------------
        # Build result
        # -------------------------------------------------------------------
        result = ControlledRuntimeAuthorizationConsumptionResult(
            request=request,
            record=record,
            freeze_gate_verified=freeze_gate_verified,
            execution_plan_verified=plan_ok,
            authorization_request_verified=auth_req_ok,
            authorization_decision_verified=auth_dec_ok,
            authorization_binding_verified=auth_bind_ok,
            prior_consumption_state_verified=prior_ok,
            policy_findings=policy_findings_tuple,
            status=status,
            recommended_action=recommended_action,
            runtime_invoked=False,
            provider_invoked=False,
            network_invoked=False,
            translation_invoked=False,
            output_written=False,
            resume_written=False,
            cache_written=False,
            retry_used=False,
            fallback_used=False,
            production_hook_invoked=False,
        )

        return result

    # -------------------------------------------------------------------
    # Internal verifiers
    # -------------------------------------------------------------------

    def _verify_freeze_gate(self, findings: _FindingCollector) -> bool:
        try:
            result = self._freeze_validator()
            if not result.valid:
                findings.add("FREEZE_GATE_FAILED", field="freeze_gate")
                return False
            return True
        except Exception:
            findings.add("FREEZE_GATE_FAILED", field="freeze_gate")
            return False

    def _verify_freeze_metadata(
        self,
        freeze_metadata: ControlledRuntimePreparationFreezeMetadata | None,
        findings: _FindingCollector,
    ) -> bool:
        if freeze_metadata is None:
            findings.add("FREEZE_METADATA_MISSING", field="freeze_metadata")
            return False
        canonical = self._freeze_metadata_provider()
        # Compare all fields
        for field_name in (
            "component_name",
            "freeze_version",
            "submission_schema_name",
            "submission_schema_version",
            "adapter_schema_name",
            "adapter_schema_version",
            "execution_plan_schema_name",
            "execution_plan_schema_version",
            "activation_gate",
            "runtime_execution_authorized",
            "provider_execution_authorized",
            "translation_execution_authorized",
            "runtime_execution_enabled",
            "provider_execution_enabled",
            "translation_execution_enabled",
            "automatic_retry_authorized",
            "automatic_fallback_authorized",
            "output_replacement_authorized",
            "output_write_authorized",
            "resume_write_authorized",
            "cache_write_authorized",
            "production_integration_authorized",
        ):
            expected = getattr(canonical, field_name)
            observed = getattr(freeze_metadata, field_name)
            if expected != observed:
                findings.add(
                    "FREEZE_DRIFT",
                    field=f"freeze_metadata.{field_name}",
                    expected=str(expected),
                    observed=str(observed),
                )
                return False
        return True

    def _verify_execution_plan(
        self,
        plan: ControlledRuntimeExecutionPlan,
        request: ControlledRuntimeAuthorizationConsumptionRequest,
        findings: _FindingCollector,
    ) -> bool:
        ok = True

        # Schema check
        if plan.schema_name != "ntpe.controlled_runtime_execution_plan":
            findings.add("PLAN_INVALID", field="plan.schema_name")
            return False
        if plan.schema_version != "1.0":
            findings.add("PLAN_INVALID", field="plan.schema_version")
            return False

        # Fingerprint match
        if plan.execution_plan_fingerprint != request.execution_plan_fingerprint:
            findings.add(
                "PLAN_FINGERPRINT_MISMATCH",
                field="execution_plan_fingerprint",
                expected=request.execution_plan_fingerprint,
                observed=plan.execution_plan_fingerprint,
            )
            return False

        # Must be single-unit plan
        if len(plan.selected_adapter_unit_indices) != 1:
            if len(plan.selected_adapter_unit_indices) > 1:
                findings.add("PLAN_MULTIPLE_SELECTED", field="selected_adapter_unit_indices")
            else:
                findings.add("PLAN_AUTO_SELECTION", field="selected_adapter_unit_indices")
            return False

        # Explicit selection required (index must be present)
        if plan.selected_adapter_unit_indices[0] != request.selected_adapter_index:
            findings.add(
                "ADAPTER_INDEX_MISMATCH",
                field="selected_adapter_index",
                expected=str(request.selected_adapter_index),
                observed=str(plan.selected_adapter_unit_indices[0]),
            )
            return False

        # Plan state checks
        if plan.execution_started:
            findings.add("PLAN_STARTED", field="execution_started")
            return False
        if plan.execution_completed:
            findings.add("PLAN_COMPLETED", field="execution_completed")
            return False
        if plan.status != "planned_not_executed":
            findings.add(
                "PLAN_WRONG_STATUS",
                field="status",
                expected="planned_not_executed",
                observed=plan.status,
            )
            return False

        # Counter checks
        if plan.provider_requests_executed != 0:
            findings.add(
                "PROVIDER_COUNTER_NONZERO",
                field="provider_requests_executed",
                expected="0",
                observed=str(plan.provider_requests_executed),
            )
            return False
        if plan.translation_executions_completed != 0:
            findings.add(
                "TRANSLATION_COUNTER_NONZERO",
                field="translation_executions_completed",
                expected="0",
                observed=str(plan.translation_executions_completed),
            )
            return False

        return ok

    def _verify_authorization_request(
        self,
        auth_req: ControlledRuntimeExecutionAuthorizationRequest,
        request: ControlledRuntimeAuthorizationConsumptionRequest,
        findings: _FindingCollector,
    ) -> bool:
        if auth_req.schema_name != "ntpe.controlled_runtime_execution_authorization_request":
            findings.add("AUTH_REQ_INVALID", field="auth_req.schema_name")
            return False
        if auth_req.schema_version != "1.0":
            findings.add("AUTH_REQ_INVALID", field="auth_req.schema_version")
            return False
        if auth_req.request_fingerprint != request.authorization_request_fingerprint:
            findings.add(
                "AUTH_REQ_FINGERPRINT_MISMATCH",
                field="authorization_request_fingerprint",
                expected=request.authorization_request_fingerprint,
                observed=auth_req.request_fingerprint,
            )
            return False
        if not auth_req.caller_confirmation:
            findings.add("AUTH_REQ_INVALID", field="caller_confirmation")
            return False
        return True

    def _verify_authorization_decision(
        self,
        auth_dec: ControlledRuntimeExecutionAuthorizationDecision,
        request: ControlledRuntimeAuthorizationConsumptionRequest,
        findings: _FindingCollector,
    ) -> bool:
        if auth_dec.schema_name != "ntpe.controlled_runtime_execution_authorization_decision":
            findings.add("AUTH_DEC_INVALID", field="auth_dec.schema_name")
            return False
        if auth_dec.schema_version != "1.0":
            findings.add("AUTH_DEC_INVALID", field="auth_dec.schema_version")
            return False
        if auth_dec.decision_fingerprint != request.authorization_decision_fingerprint:
            findings.add(
                "AUTH_DEC_FINGERPRINT_MISMATCH",
                field="authorization_decision_fingerprint",
                expected=request.authorization_decision_fingerprint,
                observed=auth_dec.decision_fingerprint,
            )
            return False
        return True

    def _verify_authorization_binding(
        self,
        auth_req: ControlledRuntimeExecutionAuthorizationRequest,
        auth_dec: ControlledRuntimeExecutionAuthorizationDecision,
        plan: ControlledRuntimeExecutionPlan,
        request: ControlledRuntimeAuthorizationConsumptionRequest,
        findings: _FindingCollector,
    ) -> bool:
        ok = True

        # Authorization ID must match
        if auth_dec.authorization_id != request.authorization_id:
            findings.add(
                "AUTHORIZATION_ID_MISMATCH",
                field="authorization_id",
                expected=request.authorization_id,
                observed=auth_dec.authorization_id,
            )
            return False

        # Must be authorized
        if not auth_dec.authorized:
            findings.add("AUTH_REJECTED", field="authorized")
            return False

        # Status must be authorized_not_executed
        if auth_dec.status != "authorized_not_executed":
            findings.add(
                "AUTH_WRONG_STATUS",
                field="status",
                expected="authorized_not_executed",
                observed=auth_dec.status,
            )
            return False

        # Already consumed check
        if auth_dec.authorization_consumed:
            findings.add("AUTH_ALREADY_CONSUMED", field="authorization_consumed")
            return False

        # Reusable check
        if auth_dec.authorization_reusable:
            findings.add("AUTH_REUSABLE", field="authorization_reusable")
            return False

        # Provider / Translation limits
        if auth_dec.authorized_provider_request_limit != 1:
            findings.add(
                "PROVIDER_LIMIT_WRONG",
                field="authorized_provider_request_limit",
                expected="1",
                observed=str(auth_dec.authorized_provider_request_limit),
            )
            return False
        if auth_dec.authorized_translation_request_limit != 1:
            findings.add(
                "TRANSLATION_LIMIT_WRONG",
                field="authorized_translation_request_limit",
                expected="1",
                observed=str(auth_dec.authorized_translation_request_limit),
            )
            return False

        # Retry / Fallback limits
        if auth_dec.authorized_retry_limit > 0:
            findings.add(
                "RETRY_LIMIT_NONZERO",
                field="authorized_retry_limit",
                expected="0",
                observed=str(auth_dec.authorized_retry_limit),
            )
            return False
        if auth_dec.authorized_fallback_limit > 0:
            findings.add(
                "FALLBACK_LIMIT_NONZERO",
                field="authorized_fallback_limit",
                expected="0",
                observed=str(auth_dec.authorized_fallback_limit),
            )
            return False

        # Additional authorizations must be false
        if auth_dec.output_replacement_authorized:
            findings.add("OUTPUT_REPLACEMENT_AUTHORIZED", field="output_replacement_authorized")
            return False
        if auth_dec.production_integration_authorized:
            findings.add(
                "PRODUCTION_INTEGRATION_AUTHORIZED", field="production_integration_authorized"
            )
            return False

        return ok

    def _verify_prior_consumption(
        self,
        auth_dec: ControlledRuntimeExecutionAuthorizationDecision,
        findings: _FindingCollector,
    ) -> bool:
        # Already validated inside _verify_authorization_binding,
        # but we double-check for explicit record state.
        if auth_dec.authorization_consumed:
            findings.add("AUTH_ALREADY_CONSUMED", field="authorization_consumed")
            return False
        return True

    def _verify_consumption_request(
        self,
        request: ControlledRuntimeAuthorizationConsumptionRequest,
        auth_dec: ControlledRuntimeExecutionAuthorizationDecision,
        plan: ControlledRuntimeExecutionPlan,
        findings: _FindingCollector,
    ) -> bool:
        ok = True

        # Consumption ID
        if not request.consumption_id or not request.consumption_id.strip():
            findings.add("EMPTY_CONSUMPTION_ID", field="consumption_id")
            return False

        # Structurally valid (non-empty, no whitespace-only, valid chars)
        cid = request.consumption_id
        if not cid.isascii():
            findings.add("MALFORMED_CONSUMPTION_ID", field="consumption_id")
            return False
        if len(cid) > 256:
            findings.add("MALFORMED_CONSUMPTION_ID", field="consumption_id")
            return False
        for ch in cid:
            if 0 <= ord(ch) <= 31 or ord(ch) == 127:
                findings.add("MALFORMED_CONSUMPTION_ID", field="consumption_id")
                return False

        # Caller confirmation
        cf = request.caller_confirmation
        if cf is True:
            pass  # ok
        elif cf is False:
            findings.add("CONFIRMATION_FALSE", field="caller_confirmation")
            return False
        else:
            findings.add("CONFIRMATION_MALFORMED", field="caller_confirmation")
            return False

        # Single execution intent
        se = request.consume_for_single_execution
        if se is True:
            pass  # ok
        elif se is False:
            findings.add("SINGLE_EXECUTION_FALSE", field="consume_for_single_execution")
            return False
        else:
            findings.add("MALFORMED_SINGLE_EXECUTION", field="consume_for_single_execution")
            return False

        # Unit count
        uc = request.requested_unit_count
        if type(uc) is bool:
            findings.add("UNIT_COUNT_BOOL", field="requested_unit_count")
            return False
        if request.requested_unit_count == 0:
            findings.add("UNIT_COUNT_ZERO", field="requested_unit_count")
            return False
        if request.requested_unit_count != 1:
            findings.add("UNIT_COUNT_GT_ONE", field="requested_unit_count")
            return False

        # Schema
        if request.schema_name != "ntpe.controlled_runtime_authorization_consumption_request":
            findings.add(
                "INVALID_REQUEST_SCHEMA",
                field="schema_name",
                expected="ntpe.controlled_runtime_authorization_consumption_request",
                observed=request.schema_name,
            )
            return False
        if request.schema_version != "1.0":
            findings.add(
                "INVALID_REQUEST_VERSION",
                field="schema_version",
                expected="1.0",
                observed=request.schema_version,
            )
            return False

        # Scope binding verification
        expected_scope = exact_consumption_scope(
            authorization_id=request.authorization_id,
            authorization_request_fingerprint=request.authorization_request_fingerprint,
            authorization_decision_fingerprint=request.authorization_decision_fingerprint,
            execution_plan_fingerprint=request.execution_plan_fingerprint,
            selected_adapter_index=request.selected_adapter_index,
            unit_count=1,
        )
        if request.consumption_scope != expected_scope:
            findings.add(
                "SCOPE_BROADER",
                field="consumption_scope",
                expected=expected_scope,
                observed=request.consumption_scope,
            )
            return False

        # Fingerprint self-check
        import hashlib
        import json
        payload = {}
        for f_name in (
            "consumption_id",
            "authorization_id",
            "authorization_request_fingerprint",
            "authorization_decision_fingerprint",
            "execution_plan_fingerprint",
            "selected_adapter_index",
            "requested_unit_count",
            "consume_for_single_execution",
            "caller_confirmation",
            "consumption_scope",
            "purpose",
            "schema_name",
            "schema_version",
        ):
            payload[f_name] = getattr(request, f_name)
        expected_fp = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        ).hexdigest()
        if request.request_fingerprint != expected_fp:
            findings.add(
                "INVALID_REQUEST_FINGERPRINT",
                field="request_fingerprint",
                expected=expected_fp,
                observed=request.request_fingerprint,
            )
            return False

        return ok

    def _verify_enablement(
        self,
        auth_dec: ControlledRuntimeExecutionAuthorizationDecision,
        plan: ControlledRuntimeExecutionPlan,
        findings: _FindingCollector,
    ) -> bool:
        ok = True

        # Enablement fields must all be false
        if auth_dec.runtime_execution_enabled:
            findings.add("RUNTIME_ENABLEMENT_TRUE", field="runtime_execution_enabled")
            ok = False
        if auth_dec.provider_execution_enabled:
            findings.add("PROVIDER_ENABLEMENT_TRUE", field="provider_execution_enabled")
            ok = False
        if auth_dec.network_execution_enabled:
            findings.add("NETWORK_ENABLEMENT_TRUE", field="network_execution_enabled")
            ok = False
        if auth_dec.translation_execution_enabled:
            findings.add("TRANSLATION_ENABLEMENT_TRUE", field="translation_execution_enabled")
            ok = False

        # Plan-level enablement must also be false
        if plan.runtime_execution_enabled:
            findings.add("RUNTIME_ENABLEMENT_TRUE", field="plan.runtime_execution_enabled")
            ok = False
        if plan.provider_execution_enabled:
            findings.add("PROVIDER_ENABLEMENT_TRUE", field="plan.provider_execution_enabled")
            ok = False
        if plan.translation_execution_enabled:
            findings.add("TRANSLATION_ENABLEMENT_TRUE", field="plan.translation_execution_enabled")
            ok = False

        # Write enablement checks (check auth_dec and plan fields directly)
        if auth_dec.output_replacement_authorized:
            findings.add("OUTPUT_REPLACEMENT_AUTHORIZED", field="output_replacement_authorized")
            ok = False
        if getattr(plan, "output_replacement_authorized", False):
            findings.add("OUTPUT_REPLACEMENT_AUTHORIZED_PLAN", field="plan.output_replacement_authorized")
            ok = False

        # Retry / Fallback — check plan authorization fields
        if getattr(plan, "automatic_retry_authorized", False):
            findings.add("RETRY_REQUESTED", field="plan.automatic_retry_authorized")
            ok = False
        if getattr(plan, "automatic_fallback_authorized", False):
            findings.add("FALLBACK_REQUESTED", field="plan.automatic_fallback_authorized")
            ok = False

        # Production hook — check auth_dec field
        if auth_dec.production_integration_authorized:
            findings.add("PRODUCTION_HOOK_REQUESTED", field="production_integration_authorized")
            ok = False

        return ok