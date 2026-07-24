"""Stage 6.4 — Controlled Runtime Execution Envelope Builder

Pure, side-effect free builder that creates an immutable execution envelope
from an authentic Stage 6.3 durable claim and all upstream artifacts.

Fail-closed: rejects any invalid state, never mutates upstream objects,
never starts Runtime, never contacts Provider or Network.
"""

from __future__ import annotations

from core.controlled_runtime_atomic_authorization_consumption.models import (
    AtomicAuthorizationConsumptionClaim,
    AtomicAuthorizationConsumptionClaimRequest,
    AtomicAuthorizationConsumptionResult,
)
from core.controlled_runtime_authorization_consumption.models import (
    ControlledRuntimeAuthorizationConsumptionRecord,
    ControlledRuntimeAuthorizationConsumptionRequest as Stage62Request,
    ControlledRuntimeAuthorizationConsumptionResult as Stage62Result,
)
from core.controlled_runtime_execution_authorization.models import (
    ControlledRuntimeExecutionAuthorizationDecision,
    ControlledRuntimeExecutionAuthorizationRequest as AuthRequest,
    ControlledRuntimeExecutionAuthorizationResult as AuthResult,
)
from core.controlled_runtime_execution_plan.models import (
    ControlledRuntimeExecutionPlan,
)

from .models import (
    ControlledRuntimeExecutionEnvelope,
    ControlledRuntimeExecutionEnvelopeFinding,
    ControlledRuntimeExecutionEnvelopeRequest,
    ControlledRuntimeExecutionEnvelopeResult,
    canonical_sha256,
)
from .policy import (
    DEFAULT_POLICY,
    FINDING_MESSAGES,
    FINDING_SEVERITIES,
    FROZEN_ACTIVATION_GATE,
    SUCCESS_ACTION,
    SUCCESS_STATUS,
    ControlledRuntimeExecutionEnvelopePolicy,
)


# ---------------------------------------------------------------------------
# Finding helpers
# ---------------------------------------------------------------------------


def _finding(
    code: str,
    *,
    field: str = "",
    expected: str = "",
    observed: str = "",
) -> ControlledRuntimeExecutionEnvelopeFinding:
    return ControlledRuntimeExecutionEnvelopeFinding(
        code=code,
        severity=FINDING_SEVERITIES.get(code, "error"),
        message=FINDING_MESSAGES.get(code, code),
        field=field,
        expected=expected,
        observed=observed,
    )


def _has_blocking(
    findings: tuple[ControlledRuntimeExecutionEnvelopeFinding, ...],
) -> bool:
    return any(f.severity == "blocking" for f in findings)


# ---------------------------------------------------------------------------
# Request validation
# ---------------------------------------------------------------------------


def _validate_request(
    request: ControlledRuntimeExecutionEnvelopeRequest,
) -> tuple[ControlledRuntimeExecutionEnvelopeFinding, ...]:
    """Validate the envelope request against all policy invariants.

    Returns a tuple of findings. Does not raise — failing closed means
    findings are collected, and the builder decides whether to reject.
    """
    findings: list[ControlledRuntimeExecutionEnvelopeFinding] = []

    # Schema
    from .models import REQUEST_SCHEMA_NAME, REQUEST_SCHEMA_VERSION

    if request.schema_name != REQUEST_SCHEMA_NAME:
        findings.append(
            _finding(
                "REQUEST_SCHEMA_MISMATCH",
                field="schema_name",
                expected=REQUEST_SCHEMA_NAME,
                observed=request.schema_name,
            )
        )
    if request.schema_version != REQUEST_SCHEMA_VERSION:
        findings.append(
            _finding(
                "REQUEST_VERSION_MISMATCH",
                field="schema_version",
                expected=REQUEST_SCHEMA_VERSION,
                observed=request.schema_version,
            )
        )

    # envelope_id
    if not request.envelope_id or not request.envelope_id.strip():
        if not request.envelope_id:
            findings.append(_finding("ENVELOPE_ID_MISSING", field="envelope_id"))
        else:
            findings.append(
                _finding(
                    "ENVELOPE_ID_BLANK",
                    field="envelope_id",
                    expected="non-blank",
                    observed=repr(request.envelope_id),
                )
            )

    # caller_confirmation
    if request.caller_confirmation is not True:
        findings.append(
            _finding(
                "CALLER_CONFIRMATION_FALSE",
                field="caller_confirmation",
                expected="True",
                observed=str(request.caller_confirmation),
            )
        )

    # runtime_handoff_requested
    if request.runtime_handoff_requested is not True:
        findings.append(
            _finding(
                "RUNTIME_HANDOFF_REQUESTED_FALSE",
                field="runtime_handoff_requested",
                expected="True",
                observed=str(request.runtime_handoff_requested),
            )
        )

    # unit count
    if request.requested_unit_count == 0:
        findings.append(
            _finding("UNIT_COUNT_ZERO", field="requested_unit_count", expected="1", observed="0")
        )
    elif request.requested_unit_count > 1:
        findings.append(
            _finding(
                "UNIT_COUNT_GREATER_THAN_ONE",
                field="requested_unit_count",
                expected="1",
                observed=str(request.requested_unit_count),
            )
        )

    # execution mode
    if request.execution_mode != "controlled_single_execution":
        findings.append(
            _finding(
                "EXECUTION_MODE_INVALID",
                field="execution_mode",
                expected="controlled_single_execution",
                observed=request.execution_mode,
            )
        )

    # runtime_scope must be non-empty
    if not request.runtime_scope or not request.runtime_scope.strip():
        findings.append(
            _finding("RUNTIME_SCOPE_INVALID", field="runtime_scope")
        )

    # purpose
    if not request.purpose or not request.purpose.strip():
        findings.append(_finding("PURPOSE_INVALID", field="purpose"))

    # Request fingerprint integrity
    actual_fp = canonical_sha256(request._fingerprint_payload())
    if actual_fp != request.request_fingerprint:
        findings.append(
            _finding(
                "REQUEST_FINGERPRINT_MISMATCH",
                field="request_fingerprint",
                expected=request.request_fingerprint,
                observed=actual_fp,
            )
        )

    return tuple(findings)


# ---------------------------------------------------------------------------
# Stage 5.4 freeze validation
# ---------------------------------------------------------------------------


def _validate_freeze(
    activation_gate: str,
    component: str,
    version: str,
) -> tuple[ControlledRuntimeExecutionEnvelopeFinding, ...]:
    """Validate Stage 5.4 freeze metadata."""
    findings: list[ControlledRuntimeExecutionEnvelopeFinding] = []

    if activation_gate != FROZEN_ACTIVATION_GATE:
        findings.append(
            _finding(
                "FREEZE_GATE_INVALID",
                field="activation_gate",
                expected=FROZEN_ACTIVATION_GATE,
                observed=activation_gate,
            )
        )

    return tuple(findings)


# ---------------------------------------------------------------------------
# Stage 5.3 plan validation
# ---------------------------------------------------------------------------


def _validate_plan(
    plan: ControlledRuntimeExecutionPlan,
    expected_fingerprint: str,
) -> tuple[ControlledRuntimeExecutionEnvelopeFinding, ...]:
    """Validate Stage 5.3 execution plan."""
    findings: list[ControlledRuntimeExecutionEnvelopeFinding] = []

    # Fingerprint matches
    if plan.execution_plan_fingerprint != expected_fingerprint:
        findings.append(
            _finding(
                "PLAN_FINGERPRINT_MISMATCH",
                field="execution_plan_fingerprint",
                expected=expected_fingerprint,
                observed=plan.execution_plan_fingerprint,
            )
        )

    # State must be planned_not_executed
    if plan.status not in frozenset({"planned_not_executed", "planned_with_warnings"}):
        findings.append(
            _finding(
                "PLAN_STATE_INVALID",
                field="status",
                expected="planned_not_executed",
                observed=plan.status,
            )
        )

    # Execution not started/completed
    if plan.execution_started:
        findings.append(_finding("PLAN_ALREADY_STARTED", field="execution_started"))
    if plan.execution_completed:
        findings.append(
            _finding("PLAN_ALREADY_COMPLETED", field="execution_completed")
        )

    # Counters must be zero
    if plan.provider_requests_executed != 0 or plan.translation_executions_completed != 0:
        findings.append(
            _finding(
                "PLAN_NONZERO_COUNTERS",
                field="providers/translations",
                expected="0/0",
                observed=f"{plan.provider_requests_executed}/{plan.translation_executions_completed}",
            )
        )

    # Exactly one selected adapter unit
    if plan.selected_adapter_unit_indices != (0,) or plan.available_adapter_unit_count != 1:
        findings.append(
            _finding(
                "PLAN_SCOPE_INVALID",
                field="selected_adapter_unit_indices",
                expected="(0,) count=1",
                observed=f"{plan.selected_adapter_unit_indices} count={plan.available_adapter_unit_count}",
            )
        )

    # Strategy must be controlled_single_unit
    if hasattr(plan, "strategy") and plan.strategy != "controlled_single_unit":
        findings.append(
            _finding(
                "PLAN_SCOPE_INVALID",
                field="strategy",
                expected="controlled_single_unit",
                observed=str(plan.strategy),
            )
        )

    # Schema name
    if plan.schema_name != "ntpe.controlled_runtime_execution_plan":
        findings.append(
            _finding(
                "PLAN_SCHEMA_MISMATCH",
                field="schema_name",
                expected="ntpe.controlled_runtime_execution_plan",
                observed=plan.schema_name,
            )
        )

    return tuple(findings)


# ---------------------------------------------------------------------------
# Stage 6.1 authorization validation
# ---------------------------------------------------------------------------


def _validate_authorization(
    auth_request: AuthRequest,
    auth_decision: ControlledRuntimeExecutionAuthorizationDecision,
    auth_result: AuthResult | None,
    *,
    expected_request_fingerprint: str,
    expected_decision_fingerprint: str,
    expected_authorization_id: str,
) -> tuple[ControlledRuntimeExecutionEnvelopeFinding, ...]:
    """Validate Stage 6.1 authorization artifacts."""
    findings: list[ControlledRuntimeExecutionEnvelopeFinding] = []

    # Request fingerprint
    if auth_request.request_fingerprint != expected_request_fingerprint:
        findings.append(
            _finding(
                "AUTH_REQUEST_FINGERPRINT_MISMATCH",
                field="authorization_request_fingerprint",
                expected=expected_request_fingerprint,
                observed=auth_request.request_fingerprint,
            )
        )

    # Decision fingerprint
    if auth_decision.decision_fingerprint != expected_decision_fingerprint:
        findings.append(
            _finding(
                "AUTH_DECISION_FINGERPRINT_MISMATCH",
                field="authorization_decision_fingerprint",
                expected=expected_decision_fingerprint,
                observed=auth_decision.decision_fingerprint,
            )
        )

    # Authorization ID
    if auth_decision.authorization_id != expected_authorization_id:
        findings.append(
            _finding(
                "AUTHORIZATION_ID_MISMATCH",
                field="authorization_id",
                expected=expected_authorization_id,
                observed=auth_decision.authorization_id,
            )
        )

    # Authorized
    if not auth_decision.authorized:
        findings.append(
            _finding(
                "AUTHORIZATION_NOT_AUTHORIZED",
                field="authorized",
                expected="True",
                observed=str(auth_decision.authorized),
            )
        )

    # Non-reusable
    if auth_decision.authorization_reusable:
        findings.append(
            _finding(
                "AUTHORIZATION_REUSABLE",
                field="authorization_reusable",
                expected="False",
                observed="True",
            )
        )

    # Status must be authorized_not_executed
    if auth_decision.status != "authorized_not_executed":
        findings.append(
            _finding(
                "AUTHORIZATION_ALREADY_EXECUTED",
                field="status",
                expected="authorized_not_executed",
                observed=auth_decision.status,
            )
        )

    # authorization_consumed must be false at this point (Stage 6.1 doesn't consume)
    if auth_decision.authorization_consumed:
        findings.append(
            _finding(
                "AUTHORIZATION_ALREADY_EXECUTED",
                field="authorization_consumed",
                expected="False",
                observed="True",
            )
        )

    # Runtime execution must not be enabled at authorization level
    if auth_decision.runtime_execution_enabled:
        findings.append(
            _finding(
                "RUNTIME_EXECUTION_ENABLED",
                field="runtime_execution_enabled",
                expected="False",
                observed="True",
            )
        )

    # Verify result if provided
    if auth_result is not None:
        if auth_result.status != "authorized_not_executed":
            findings.append(
                _finding(
                    "AUTHORIZATION_DECISION_INVALID",
                    field="auth_result.status",
                    expected="authorized_not_executed",
                    observed=auth_result.status,
                )
            )

    return tuple(findings)


# ---------------------------------------------------------------------------
# Stage 6.2 consumption validation
# ---------------------------------------------------------------------------


def _validate_stage62(
    stage62_request: Stage62Request,
    stage62_record: ControlledRuntimeAuthorizationConsumptionRecord,
    stage62_result: Stage62Result | None,
    *,
    expected_request_fingerprint: str,
    expected_record_fingerprint: str,
    expected_consumption_id: str,
) -> tuple[ControlledRuntimeExecutionEnvelopeFinding, ...]:
    """Validate Stage 6.2 consumption artifacts."""
    findings: list[ControlledRuntimeExecutionEnvelopeFinding] = []

    # Request fingerprint
    if stage62_request.request_fingerprint != expected_request_fingerprint:
        findings.append(
            _finding(
                "STAGE62_REQUEST_FINGERPRINT_MISMATCH",
                field="stage62_request_fingerprint",
                expected=expected_request_fingerprint,
                observed=stage62_request.request_fingerprint,
            )
        )

    # Record fingerprint
    if stage62_record.record_fingerprint != expected_record_fingerprint:
        findings.append(
            _finding(
                "STAGE62_RECORD_FINGERPRINT_MISMATCH",
                field="stage62_record_fingerprint",
                expected=expected_record_fingerprint,
                observed=stage62_record.record_fingerprint,
            )
        )

    # Consumption ID
    if stage62_record.consumption_id != expected_consumption_id:
        findings.append(
            _finding(
                "CONSUMPTION_ID_MISMATCH",
                field="consumption_id",
                expected=expected_consumption_id,
                observed=stage62_record.consumption_id,
            )
        )

    # Prepared
    if not stage62_record.authorization_consumption_prepared:
        findings.append(
            _finding(
                "STAGE62_NOT_PREPARED",
                field="authorization_consumption_prepared",
                expected="True",
                observed="False",
            )
        )

    # NOT consumed
    if stage62_record.authorization_consumed:
        findings.append(
            _finding(
                "STAGE62_ALREADY_CONSUMED",
                field="authorization_consumed",
                expected="False",
                observed="True",
            )
        )

    # durable_reuse_prevention_established must be false (Stage 6.2 doesn't do durable)
    if stage62_record.durable_reuse_prevention_established:
        findings.append(
            _finding(
                "STAGE62_FALSE_DURABLE_CLAIM",
                field="durable_reuse_prevention_established",
                expected="False",
                observed="True",
            )
        )

    # persistent_registry_written must be false
    if stage62_record.persistent_registry_written:
        findings.append(
            _finding(
                "STAGE62_FALSE_REGISTRY_CLAIM",
                field="persistent_registry_written",
                expected="False",
                observed="True",
            )
        )

    # Status
    if stage62_record.status != "consumption_prepared_not_executed":
        findings.append(
            _finding(
                "STAGE62_RECORD_INVALID",
                field="status",
                expected="consumption_prepared_not_executed",
                observed=stage62_record.status,
            )
        )

    # Capabilities must be off
    if stage62_record.runtime_execution_enabled:
        findings.append(_finding("RUNTIME_EXECUTION_ENABLED"))
    if stage62_record.provider_execution_enabled:
        findings.append(_finding("PROVIDER_EXECUTION_ENABLED"))
    if stage62_record.network_execution_enabled:
        findings.append(_finding("NETWORK_EXECUTION_ENABLED"))
    if stage62_record.translation_execution_enabled:
        findings.append(_finding("TRANSLATION_EXECUTION_ENABLED"))
    if stage62_record.output_write_enabled:
        findings.append(_finding("OUTPUT_WRITE_ENABLED"))
    if stage62_record.resume_write_enabled:
        findings.append(_finding("RESUME_WRITE_ENABLED"))
    if stage62_record.cache_write_enabled:
        findings.append(_finding("CACHE_WRITE_ENABLED"))
    if stage62_record.retry_enabled:
        findings.append(_finding("RETRY_ENABLED"))
    if stage62_record.fallback_enabled:
        findings.append(_finding("FALLBACK_ENABLED"))
    if stage62_record.production_hook_enabled:
        findings.append(_finding("PRODUCTION_HOOK_ENABLED"))

    return tuple(findings)


# ---------------------------------------------------------------------------
# Stage 6.3 claim validation
# ---------------------------------------------------------------------------


def _validate_stage63(
    claim_request: AtomicAuthorizationConsumptionClaimRequest,
    claim: AtomicAuthorizationConsumptionClaim,
    stage63_result: AtomicAuthorizationConsumptionResult | None,
    *,
    expected_claim_request_fingerprint: str,
    expected_claim_fingerprint: str,
    expected_claim_id: str,
    stage62_request: Stage62Request | None = None,
    stage62_record: ControlledRuntimeAuthorizationConsumptionRecord | None = None,
    auth_request: AuthRequest | None = None,
    auth_decision: ControlledRuntimeExecutionAuthorizationDecision | None = None,
) -> tuple[ControlledRuntimeExecutionEnvelopeFinding, ...]:
    """Validate Stage 6.3 durable claim artifacts."""
    findings: list[ControlledRuntimeExecutionEnvelopeFinding] = []

    # Claim request fingerprint
    if claim_request.request_fingerprint != expected_claim_request_fingerprint:
        findings.append(
            _finding(
                "STAGE63_CLAIM_REQUEST_FINGERPRINT_MISMATCH",
                field="stage63_claim_request_fingerprint",
                expected=expected_claim_request_fingerprint,
                observed=claim_request.request_fingerprint,
            )
        )

    # Claim fingerprint
    if claim.claim_fingerprint != expected_claim_fingerprint:
        findings.append(
            _finding(
                "STAGE63_CLAIM_FINGERPRINT_MISMATCH",
                field="stage63_claim_fingerprint",
                expected=expected_claim_fingerprint,
                observed=claim.claim_fingerprint,
            )
        )

    # Claim ID
    if claim.claim_id != expected_claim_id:
        findings.append(
            _finding(
                "CLAIM_ID_MISMATCH",
                field="claim_id",
                expected=expected_claim_id,
                observed=claim.claim_id,
            )
        )

    # Cross-stage: claim's internal stage62 fingerprints must match actual stage62 artifacts
    if stage62_request is not None and claim.stage62_request_fingerprint != stage62_request.request_fingerprint:
        findings.append(
            _finding(
                "STAGE62_REQUEST_FINGERPRINT_MISMATCH",
                field="claim.stage62_request_fingerprint",
                expected=stage62_request.request_fingerprint,
                observed=claim.stage62_request_fingerprint,
            )
        )

    if stage62_record is not None and claim.stage62_record_fingerprint != stage62_record.record_fingerprint:
        findings.append(
            _finding(
                "STAGE62_RECORD_FINGERPRINT_MISMATCH",
                field="claim.stage62_record_fingerprint",
                expected=stage62_record.record_fingerprint,
                observed=claim.stage62_record_fingerprint,
            )
        )

    # Cross-stage: claim's internal authorization fingerprints must match actual auth artifacts
    if auth_request is not None and claim.authorization_request_fingerprint != auth_request.request_fingerprint:
        findings.append(
            _finding(
                "AUTHORIZATION_REQUEST_FINGERPRINT_MISMATCH",
                field="claim.authorization_request_fingerprint",
                expected=auth_request.request_fingerprint,
                observed=claim.authorization_request_fingerprint,
            )
        )

    if auth_decision is not None and claim.authorization_decision_fingerprint != auth_decision.decision_fingerprint:
        findings.append(
            _finding(
                "AUTHORIZATION_DECISION_FINGERPRINT_MISMATCH",
                field="claim.authorization_decision_fingerprint",
                expected=auth_decision.decision_fingerprint,
                observed=claim.authorization_decision_fingerprint,
            )
        )

    # authorization_consumed must be true
    if not claim.authorization_consumed:
        findings.append(
            _finding(
                "STAGE63_AUTHORIZATION_NOT_CONSUMED",
                field="authorization_consumed",
                expected="True",
                observed="False",
            )
        )

    # authorization_reusable must be false
    if claim.authorization_reusable:
        findings.append(
            _finding(
                "STAGE63_AUTHORIZATION_REUSABLE",
                field="authorization_reusable",
                expected="False",
                observed="True",
            )
        )

    # durable_reuse_prevention_established must be true
    if not claim.durable_reuse_prevention_established:
        findings.append(
            _finding(
                "STAGE63_DURABLE_PREVENTION_FALSE",
                field="durable_reuse_prevention_established",
                expected="True",
                observed="False",
            )
        )

    # persistent_registry_written must be true
    if not claim.persistent_registry_written:
        findings.append(
            _finding(
                "STAGE63_REGISTRY_WRITTEN_FALSE",
                field="persistent_registry_written",
                expected="True",
                observed="False",
            )
        )

    # execution_started must be false
    if claim.execution_started:
        findings.append(
            _finding("STAGE63_EXECUTION_STARTED", field="execution_started")
        )

    # execution_completed must be false
    if claim.execution_completed:
        findings.append(
            _finding("STAGE63_EXECUTION_COMPLETED", field="execution_completed")
        )

    # claim state
    if claim.claim_state != "durably_consumed_not_executed":
        findings.append(
            _finding(
                "STAGE63_CLAIM_INVALID",
                field="claim_state",
                expected="durably_consumed_not_executed",
                observed=claim.claim_state,
            )
        )

    # All execution/write enablements must be false
    if claim.runtime_execution_enabled:
        findings.append(_finding("RUNTIME_EXECUTION_ENABLED"))
    if claim.provider_execution_enabled:
        findings.append(_finding("PROVIDER_EXECUTION_ENABLED"))
    if claim.network_execution_enabled:
        findings.append(_finding("NETWORK_EXECUTION_ENABLED"))
    if claim.translation_execution_enabled:
        findings.append(_finding("TRANSLATION_EXECUTION_ENABLED"))
    if claim.output_write_enabled:
        findings.append(_finding("OUTPUT_WRITE_ENABLED"))
    if claim.resume_write_enabled:
        findings.append(_finding("RESUME_WRITE_ENABLED"))
    if claim.cache_write_enabled:
        findings.append(_finding("CACHE_WRITE_ENABLED"))
    if claim.retry_enabled:
        findings.append(_finding("RETRY_ENABLED"))
    if claim.fallback_enabled:
        findings.append(_finding("FALLBACK_ENABLED"))
    if claim.production_hook_enabled:
        findings.append(_finding("PRODUCTION_HOOK_ENABLED"))

    # Verify result if provided
    if stage63_result is not None:
        if not stage63_result.atomic_claim_committed:
            findings.append(
                _finding(
                    "STAGE63_ATOMIC_CLAIM_NOT_COMMITTED",
                    field="atomic_claim_committed",
                    expected="True",
                    observed="False",
                )
            )
        if stage63_result.duplicate_claim_detected:
            findings.append(
                _finding(
                    "STAGE63_DUPLICATE_CLAIM_DETECTED",
                    field="duplicate_claim_detected",
                    expected="False",
                    observed="True",
                )
            )
        if stage63_result.status != "durably_consumed_not_executed":
            findings.append(
                _finding(
                    "STAGE63_RESULT_INVALID",
                    field="status",
                    expected="durably_consumed_not_executed",
                    observed=stage63_result.status,
                )
            )

    return tuple(findings)


# ---------------------------------------------------------------------------
# Fingerprint chain validation
# ---------------------------------------------------------------------------


def _validate_upstream_chain(
    claim: AtomicAuthorizationConsumptionClaim,
    *,
    expected_chain: tuple[str, ...] | None = None,
) -> tuple[ControlledRuntimeExecutionEnvelopeFinding, ...]:
    """Validate the upstream fingerprint chain from the Stage 6.3 claim.

    The claim's upstream_fingerprint_chain should contain 12 pre-claim layers
    plus the claim itself as the 13th (tip). The builder will later add
    layer 14 (envelope request) to form the complete 14-layer pre-envelope
    chain for the envelope model.
    """
    findings: list[ControlledRuntimeExecutionEnvelopeFinding] = []

    chain = claim.upstream_fingerprint_chain
    expected_claim_layers = 13  # 12 pre-claim + claim tip == 13

    if len(chain) != expected_claim_layers:
        findings.append(
            _finding(
                "UPSTREAM_FINGERPRINT_CHAIN_MISMATCH",
                field="upstream_fingerprint_chain",
                expected=f"{expected_claim_layers} layers",
                observed=f"{len(chain)} layers",
            )
        )

    if expected_chain is not None and chain != expected_chain:
        findings.append(
            _finding("UPSTREAM_FINGERPRINT_CHAIN_ALTERED", field="upstream_fingerprint_chain")
        )

    return tuple(findings)


# ---------------------------------------------------------------------------
# Adapter index / binding validation
# ---------------------------------------------------------------------------


def _validate_bindings(
    request: ControlledRuntimeExecutionEnvelopeRequest,
    plan: ControlledRuntimeExecutionPlan,
    claim: AtomicAuthorizationConsumptionClaim,
    stage62_record: ControlledRuntimeAuthorizationConsumptionRecord,
) -> tuple[ControlledRuntimeExecutionEnvelopeFinding, ...]:
    """Validate cross-artifact bindings: adapter index, unit count, scope."""
    findings: list[ControlledRuntimeExecutionEnvelopeFinding] = []

    # Adapter index cross-check
    expected_adapter = plan.selected_adapter_unit_indices[0] if plan.selected_adapter_unit_indices else 0
    if request.selected_adapter_index != expected_adapter:
        findings.append(
            _finding(
                "ADAPTER_INDEX_MISMATCH",
                field="selected_adapter_index",
                expected=str(expected_adapter),
                observed=str(request.selected_adapter_index),
            )
        )

    if claim.selected_adapter_index != expected_adapter:
        findings.append(
            _finding(
                "ADAPTER_INDEX_MISMATCH",
                field="claim.selected_adapter_index",
                expected=str(expected_adapter),
                observed=str(claim.selected_adapter_index),
            )
        )

    if stage62_record.selected_adapter_index != expected_adapter:
        findings.append(
            _finding(
                "ADAPTER_INDEX_MISMATCH",
                field="stage62.selected_adapter_index",
                expected=str(expected_adapter),
                observed=str(stage62_record.selected_adapter_index),
            )
        )

    return tuple(findings)


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------


class ControlledRuntimeExecutionEnvelopeBuilder:
    """Pure, fail-closed builder for a Controlled Runtime Execution Envelope.

    Accepts all upstream authentic immutable artifacts and a validated
    request. Produces an immutable envelope result.

    Does NOT:
    - start Runtime
    - call Provider
    - contact Network
    - translate
    - write output / resume / cache
    - create threads or subprocesses
    - mutate upstream objects
    - write to the Stage 6.3 registry
    """

    def __init__(
        self,
        *,
        policy: ControlledRuntimeExecutionEnvelopePolicy = DEFAULT_POLICY,
    ) -> None:
        self._policy = policy

    def build(
        self,
        *,
        request: ControlledRuntimeExecutionEnvelopeRequest,
        plan: ControlledRuntimeExecutionPlan,
        activation_gate: str,
        freeze_component: str = "controlled_runtime_preparation",
        freeze_version: str = "1.0",
        auth_request: AuthRequest,
        auth_decision: ControlledRuntimeExecutionAuthorizationDecision,
        auth_result: AuthResult | None = None,
        stage62_request: Stage62Request,
        stage62_record: ControlledRuntimeAuthorizationConsumptionRecord,
        stage62_result: Stage62Result | None = None,
        stage63_claim_request: AtomicAuthorizationConsumptionClaimRequest,
        stage63_claim: AtomicAuthorizationConsumptionClaim,
        stage63_result: AtomicAuthorizationConsumptionResult | None = None,
    ) -> ControlledRuntimeExecutionEnvelopeResult:
        """Build the execution envelope or fail closed.

        Returns a ControlledRuntimeExecutionEnvelopeResult.
        Never raises for policy violations — findings drive status and action.
        Raises ControlledRuntimeExecutionEnvelopeBuildError only for
        schema-level violations where an envelope cannot be represented.
        """
        all_findings: list[ControlledRuntimeExecutionEnvelopeFinding] = []
        result_flags: dict[str, bool] = {
            "freeze_gate_verified": True,
            "execution_plan_verified": True,
            "authorization_request_verified": True,
            "authorization_decision_verified": True,
            "stage62_request_verified": True,
            "stage62_record_verified": True,
            "stage62_result_verified": True,
            "stage63_claim_request_verified": True,
            "stage63_claim_verified": True,
            "stage63_result_verified": True,
            "authorization_binding_verified": True,
            "consumption_binding_verified": True,
            "durable_claim_binding_verified": True,
            "execution_unit_verified": True,
            "runtime_scope_verified": True,
        }

        # 1. Validate request
        req_findings = _validate_request(request)
        all_findings.extend(req_findings)
        if any(f.severity in ("blocking",) for f in req_findings):
            # Do not proceed — select status based on findings
            return self._reject(
                request=request,
                findings=tuple(all_findings),
                result_flags=result_flags,
            )

        # 2. Validate freeze
        freeze_findings = _validate_freeze(activation_gate, freeze_component, freeze_version)
        all_findings.extend(freeze_findings)
        if any(f.severity in ("blocking",) for f in freeze_findings):
            result_flags["freeze_gate_verified"] = False

        # 3. Validate plan
        plan_findings = _validate_plan(plan, request.execution_plan_fingerprint)
        all_findings.extend(plan_findings)
        if any(f.severity == "blocking" for f in plan_findings):
            result_flags["execution_plan_verified"] = False
        if any(f.severity == "error" for f in plan_findings) and not _has_blocking(plan_findings):
            result_flags["execution_plan_verified"] = False

        # 4. Validate authorization
        auth_findings = _validate_authorization(
            auth_request,
            auth_decision,
            auth_result,
            expected_request_fingerprint=request.authorization_request_fingerprint,
            expected_decision_fingerprint=request.authorization_decision_fingerprint,
            expected_authorization_id=request.authorization_id,
        )
        all_findings.extend(auth_findings)
        if any(f.severity == "blocking" for f in auth_findings):
            result_flags["authorization_request_verified"] = False
            result_flags["authorization_decision_verified"] = False

        # 5. Validate Stage 6.2
        stage62_findings = _validate_stage62(
            stage62_request,
            stage62_record,
            stage62_result,
            expected_request_fingerprint=request.stage62_request_fingerprint,
            expected_record_fingerprint=request.stage62_record_fingerprint,
            expected_consumption_id=request.consumption_id,
        )
        all_findings.extend(stage62_findings)
        if any(f.severity == "blocking" for f in stage62_findings):
            result_flags["stage62_request_verified"] = False
            result_flags["stage62_record_verified"] = False

        # 6. Validate Stage 6.3 claim
        stage63_findings = _validate_stage63(
            stage63_claim_request,
            stage63_claim,
            stage63_result,
            expected_claim_request_fingerprint=request.stage63_claim_request_fingerprint,
            expected_claim_fingerprint=request.stage63_claim_fingerprint,
            expected_claim_id=request.claim_id,
            stage62_request=stage62_request,
            stage62_record=stage62_record,
            auth_request=auth_request,
            auth_decision=auth_decision,
        )
        all_findings.extend(stage63_findings)
        if any(f.severity == "blocking" for f in stage63_findings):
            result_flags["stage63_claim_request_verified"] = False
            result_flags["stage63_claim_verified"] = False

        # 7. Validate upstream fingerprint chain
        chain_findings = _validate_upstream_chain(stage63_claim)
        all_findings.extend(chain_findings)
        if any(f.severity == "blocking" for f in chain_findings):
            result_flags["authorization_binding_verified"] = False
            result_flags["consumption_binding_verified"] = False
            result_flags["durable_claim_binding_verified"] = False

        # 8. Validate cross-artifact bindings
        binding_findings = _validate_bindings(
            request, plan, stage63_claim, stage62_record
        )
        all_findings.extend(binding_findings)
        if any(f.severity == "blocking" for f in binding_findings):
            result_flags["execution_unit_verified"] = False
            result_flags["runtime_scope_verified"] = False

        # 9. Any blocking finding → reject
        if _has_blocking(tuple(all_findings)):
            return self._reject(
                request=request,
                findings=tuple(all_findings),
                result_flags=result_flags,
            )

        # 10. Success — build the envelope
        # Compute the upstream chain: 13 from Stage 6.3 claim
        # + envelope request fingerprint = 14 pre-envelope layers
        claim_chain = tuple(stage63_claim.upstream_fingerprint_chain)
        if len(claim_chain) != 13:
            return self._reject(
                request=request,
                findings=tuple(all_findings) + (
                    _finding(
                        "UPSTREAM_FINGERPRINT_CHAIN_MISMATCH",
                        field="claim_chain_length",
                        expected="13",
                        observed=str(len(claim_chain)),
                    ),
                ),
                result_flags=result_flags,
            )
        upstream_chain = claim_chain + (request.request_fingerprint,)

        envelope = ControlledRuntimeExecutionEnvelope(
            envelope_id=request.envelope_id,
            claim_id=request.claim_id,
            consumption_id=request.consumption_id,
            authorization_id=request.authorization_id,
            authorization_request_fingerprint=request.authorization_request_fingerprint,
            authorization_decision_fingerprint=request.authorization_decision_fingerprint,
            execution_plan_fingerprint=request.execution_plan_fingerprint,
            stage62_request_fingerprint=request.stage62_request_fingerprint,
            stage62_record_fingerprint=request.stage62_record_fingerprint,
            stage63_claim_request_fingerprint=request.stage63_claim_request_fingerprint,
            stage63_claim_fingerprint=request.stage63_claim_fingerprint,
            selected_adapter_index=request.selected_adapter_index,
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
            upstream_fingerprint_chain=upstream_chain,
            envelope_request_fingerprint=request.request_fingerprint,
        )

        result = ControlledRuntimeExecutionEnvelopeResult(
            request=request,
            envelope=envelope,
            freeze_gate_verified=result_flags["freeze_gate_verified"],
            execution_plan_verified=result_flags["execution_plan_verified"],
            authorization_request_verified=result_flags["authorization_request_verified"],
            authorization_decision_verified=result_flags["authorization_decision_verified"],
            stage62_request_verified=result_flags["stage62_request_verified"],
            stage62_record_verified=result_flags["stage62_record_verified"],
            stage62_result_verified=result_flags["stage62_result_verified"],
            stage63_claim_request_verified=result_flags["stage63_claim_request_verified"],
            stage63_claim_verified=result_flags["stage63_claim_verified"],
            stage63_result_verified=result_flags["stage63_result_verified"],
            authorization_binding_verified=result_flags["authorization_binding_verified"],
            consumption_binding_verified=result_flags["consumption_binding_verified"],
            durable_claim_binding_verified=result_flags["durable_claim_binding_verified"],
            execution_unit_verified=result_flags["execution_unit_verified"],
            runtime_scope_verified=result_flags["runtime_scope_verified"],
            policy_findings=tuple(all_findings),
            status=SUCCESS_STATUS,
            recommended_action=SUCCESS_ACTION,
        )
        return result

    def _reject(
        self,
        *,
        request: ControlledRuntimeExecutionEnvelopeRequest,
        findings: tuple[ControlledRuntimeExecutionEnvelopeFinding, ...],
        result_flags: dict[str, bool],
    ) -> ControlledRuntimeExecutionEnvelopeResult:
        """Build a rejection result — no envelope."""
        status = self._determine_rejection_status(findings)
        action = self._determine_rejection_action(status)
        return ControlledRuntimeExecutionEnvelopeResult(
            request=request,
            envelope=None,
            freeze_gate_verified=result_flags.get("freeze_gate_verified", False),
            execution_plan_verified=result_flags.get("execution_plan_verified", False),
            authorization_request_verified=result_flags.get("authorization_request_verified", False),
            authorization_decision_verified=result_flags.get("authorization_decision_verified", False),
            stage62_request_verified=result_flags.get("stage62_request_verified", False),
            stage62_record_verified=result_flags.get("stage62_record_verified", False),
            stage62_result_verified=result_flags.get("stage62_result_verified", False),
            stage63_claim_request_verified=result_flags.get("stage63_claim_request_verified", False),
            stage63_claim_verified=result_flags.get("stage63_claim_verified", False),
            stage63_result_verified=result_flags.get("stage63_result_verified", False),
            authorization_binding_verified=result_flags.get("authorization_binding_verified", False),
            consumption_binding_verified=result_flags.get("consumption_binding_verified", False),
            durable_claim_binding_verified=result_flags.get("durable_claim_binding_verified", False),
            execution_unit_verified=result_flags.get("execution_unit_verified", False),
            runtime_scope_verified=result_flags.get("runtime_scope_verified", False),
            policy_findings=findings,
            status=status,
            recommended_action=action,
        )

    @staticmethod
    def _determine_rejection_status(
        findings: tuple[ControlledRuntimeExecutionEnvelopeFinding, ...],
    ) -> str:
        codes = {f.code for f in findings}
        # Routing decisions
        if any(
            c in codes
            for c in (
                "ENVELOPE_ID_MISSING",
                "ENVELOPE_ID_BLANK",
                "ENVELOPE_ID_INVALID",
                "CALLER_CONFIRMATION_FALSE",
                "RUNTIME_HANDOFF_REQUESTED_FALSE",
                "EXECUTION_MODE_INVALID",
                "UNIT_COUNT_ZERO",
                "UNIT_COUNT_GREATER_THAN_ONE",
                "UNIT_COUNT_TYPE_INVALID",
                "REQUEST_FINGERPRINT_MISMATCH",
                "REQUEST_SCHEMA_MISMATCH",
                "REQUEST_VERSION_MISMATCH",
            )
        ):
            return "invalid_request"
        if any(
            c in codes
            for c in (
                "CLAIM_ID_MISMATCH",
                "CONSUMPTION_ID_MISMATCH",
                "AUTHORIZATION_ID_MISMATCH",
                "AUTH_REQUEST_FINGERPRINT_MISMATCH",
                "AUTH_DECISION_FINGERPRINT_MISMATCH",
                "EXECUTION_PLAN_FINGERPRINT_MISMATCH",
                "STAGE62_REQUEST_FINGERPRINT_MISMATCH",
                "STAGE62_RECORD_FINGERPRINT_MISMATCH",
                "STAGE63_CLAIM_REQUEST_FINGERPRINT_MISMATCH",
                "STAGE63_CLAIM_FINGERPRINT_MISMATCH",
                "UPSTREAM_FINGERPRINT_CHAIN_MISMATCH",
                "UPSTREAM_FINGERPRINT_CHAIN_ALTERED",
                "PLAN_FINGERPRINT_MISMATCH",
                "PLAN_SCHEMA_MISMATCH",
                "FREEZE_GATE_INVALID",
                "FREEZE_VALIDATION_FAILED",
                "STAGE62_FALSE_DURABLE_CLAIM",
                "STAGE62_FALSE_REGISTRY_CLAIM",
                "AUTHORIZATION_REQUEST_INVALID",
                "AUTHORIZATION_DECISION_INVALID",
                "STAGE62_REQUEST_INVALID",
                "STAGE62_RECORD_INVALID",
                "STAGE63_CLAIM_REQUEST_INVALID",
                "STAGE63_CLAIM_INVALID",
            )
        ):
            return "upstream_contract_mismatch"
        if any(
            c in codes
            for c in (
                "STAGE63_AUTHORIZATION_NOT_CONSUMED",
                "STAGE63_AUTHORIZATION_REUSABLE",
                "AUTHORIZATION_NOT_AUTHORIZED",
                "AUTHORIZATION_REUSABLE",
                "AUTHORIZATION_ALREADY_EXECUTED",
                "STAGE62_NOT_PREPARED",
                "STAGE62_ALREADY_CONSUMED",
                "STAGE63_RESULT_INVALID",
                "STAGE62_RESULT_INVALID",
            )
        ):
            return "authorization_not_consumed"
        if any(
            c in codes
            for c in (
                "STAGE63_DURABLE_PREVENTION_FALSE",
                "STAGE63_REGISTRY_WRITTEN_FALSE",
                "STAGE63_DUPLICATE_CLAIM_DETECTED",
                "STAGE63_ATOMIC_CLAIM_NOT_COMMITTED",
            )
        ):
            return "durable_claim_mismatch"
        if any(
            c in codes
            for c in (
                "PLAN_SCOPE_INVALID",
                "ADAPTER_INDEX_MISMATCH",
                "RUNTIME_SCOPE_INVALID",
            )
        ):
            return "execution_scope_mismatch"
        if any(
            c in codes
            for c in (
                "PLAN_STATE_INVALID",
                "PLAN_ALREADY_STARTED",
                "PLAN_ALREADY_COMPLETED",
                "STAGE63_EXECUTION_STARTED",
                "STAGE63_EXECUTION_COMPLETED",
            )
        ):
            return "execution_unit_mismatch"
        if any(
            c in codes
            for c in (
                "RUNTIME_EXECUTION_ENABLED",
                "PROVIDER_EXECUTION_ENABLED",
                "NETWORK_EXECUTION_ENABLED",
                "TRANSLATION_EXECUTION_ENABLED",
                "OUTPUT_WRITE_ENABLED",
                "RESUME_WRITE_ENABLED",
                "CACHE_WRITE_ENABLED",
                "RETRY_ENABLED",
                "FALLBACK_ENABLED",
                "PRODUCTION_HOOK_ENABLED",
                "RUNTIME_HANDOFF_ALREADY_COMPLETED",
                "PLAN_NONZERO_COUNTERS",
            )
        ):
            return "runtime_handoff_not_eligible"
        if codes:
            return "verification_failed"
        return "rejected"

    @staticmethod
    def _determine_rejection_action(status: str) -> str:
        _action_map: dict[str, str] = {
            "invalid_request": "correct_request",
            "upstream_contract_mismatch": "rebuild_from_frozen_contract",
            "authorization_not_consumed": "rebuild_from_frozen_contract",
            "durable_claim_mismatch": "manual_integrity_review",
            "execution_scope_mismatch": "correct_request",
            "execution_unit_mismatch": "manual_integrity_review",
            "runtime_handoff_not_eligible": "do_not_execute",
            "verification_failed": "manual_integrity_review",
            "rejected": "reject",
        }
        return _action_map.get(status, "reject")