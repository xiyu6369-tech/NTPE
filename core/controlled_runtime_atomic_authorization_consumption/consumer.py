"""Stage 6.3 durable claim orchestrator; it never executes authorized work."""

from __future__ import annotations

import json
from dataclasses import fields
from hashlib import sha256
from pathlib import Path

from core.controlled_runtime_authorization_consumption import verify_consumption_record
from core.controlled_runtime_execution_plan import (
    get_controlled_runtime_preparation_freeze_metadata,
    validate_controlled_runtime_preparation_freeze,
)

from .errors import (
    AtomicConsumptionAlreadyConsumedError,
    AtomicConsumptionCommitError,
    AtomicConsumptionRegistryIntegrityError,
    AtomicConsumptionRegistryPathError,
    AtomicConsumptionRegistrySchemaError,
)
from .models import (
    AtomicAuthorizationConsumptionClaim,
    AtomicAuthorizationConsumptionClaimRequest,
    AtomicAuthorizationConsumptionFinding,
    AtomicAuthorizationConsumptionResult,
    canonical_json,
    canonical_sha256,
)
from .policy import AtomicAuthorizationConsumptionPolicy
from .registry import AtomicAuthorizationConsumptionRegistry
from .verification import verify_atomic_consumption_claim


def _hash_json(payload: object) -> str:
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


class AtomicAuthorizationConsumer:
    """Authenticate one prepared authorization and durably claim it once."""

    def __init__(self, policy: AtomicAuthorizationConsumptionPolicy | None = None) -> None:
        self.policy = policy or AtomicAuthorizationConsumptionPolicy()

    def consume(
        self,
        *,
        request: AtomicAuthorizationConsumptionClaimRequest,
        execution_plan: object,
        freeze_metadata: object,
        authorization_request: object,
        authorization_decision: object,
        stage62_request: object,
        stage62_record: object,
        stage62_result: object,
        registry_path: str | Path | None = None,
        allowed_root: str | Path | None = None,
        registry: AtomicAuthorizationConsumptionRegistry | None = None,
    ) -> AtomicAuthorizationConsumptionResult:
        flags = {
            "freeze_gate_verified": False, "execution_plan_verified": False,
            "authorization_request_verified": False, "authorization_decision_verified": False,
            "stage62_request_verified": False, "stage62_record_verified": False,
            "stage62_result_verified": False, "authorization_binding_verified": False,
            "consumption_binding_verified": False, "registry_path_verified": False,
            "registry_schema_verified": False,
        }
        findings: list[AtomicAuthorizationConsumptionFinding] = []

        def reject(code: str, status: str = "upstream_contract_mismatch") -> AtomicAuthorizationConsumptionResult:
            findings.append(AtomicAuthorizationConsumptionFinding(code, "blocking", code.replace("_", " ").lower()))
            action = {
                "invalid_request": "correct_request",
                "registry_path_rejected": "reject",
                "registry_schema_mismatch": "repair_or_replace_registry",
                "registry_integrity_failure": "manual_integrity_review",
                "claim_verification_failed": "manual_integrity_review",
                "atomic_commit_failed": "manual_integrity_review",
            }.get(status, "rebuild_from_frozen_contract")
            return self._result(request, None, flags, tuple(findings), status, action)

        # Validate the Stage 6.3 request itself, including exact bool/int semantics.
        if request.request_fingerprint != canonical_sha256(request._fingerprint_payload()):
            return reject("INVALID_REQUEST_FINGERPRINT", "invalid_request")
        if request.caller_confirmation is not True or request.claim_for_single_execution is not True:
            return reject("CLAIM_CONFIRMATION_REQUIRED", "invalid_request")
        if type(request.requested_unit_count) is not int or request.requested_unit_count != 1:
            return reject("UNIT_COUNT_MUST_EQUAL_ONE", "invalid_request")

        try:
            registry = registry or AtomicAuthorizationConsumptionRegistry(
                registry_path, allowed_root, busy_timeout_ms=self.policy.sqlite_busy_timeout_ms  # type: ignore[arg-type]
            )
        except (AtomicConsumptionRegistryPathError, TypeError, ValueError):
            return reject("REGISTRY_PATH_REJECTED", "registry_path_rejected")
        flags["registry_path_verified"] = True
        if request.registry_scope != registry.registry_scope:
            return reject("REGISTRY_SCOPE_MISMATCH", "invalid_request")

        try:
            gate = validate_controlled_runtime_preparation_freeze()
            flags["freeze_gate_verified"] = bool(getattr(gate, "valid", False)) and (
                freeze_metadata == get_controlled_runtime_preparation_freeze_metadata()
            )
        except Exception:
            flags["freeze_gate_verified"] = False
        if not flags["freeze_gate_verified"]:
            return reject("FREEZE_GATE_FAILED")

        plan_ok = all((
            getattr(execution_plan, "activation_gate", None) == "controlled_runtime_preparation_frozen",
            getattr(execution_plan, "status", None) == "planned_not_executed",
            getattr(execution_plan, "execution_started", None) is False,
            getattr(execution_plan, "execution_completed", None) is False,
            getattr(execution_plan, "provider_requests_executed", None) == 0,
            getattr(execution_plan, "translation_executions_completed", None) == 0,
            len(getattr(execution_plan, "selected_adapter_unit_indices", ())) == 1,
            getattr(execution_plan, "execution_plan_fingerprint", None) == request.execution_plan_fingerprint,
        ))
        flags["execution_plan_verified"] = plan_ok
        if not plan_ok:
            return reject("EXECUTION_PLAN_INVALID")

        try:
            auth_req_fp = _hash_json(authorization_request.fingerprint_payload())
        except Exception:
            auth_req_fp = ""
        flags["authorization_request_verified"] = auth_req_fp == getattr(authorization_request, "request_fingerprint", None)
        decision_payload = {
            item.name: getattr(authorization_decision, item.name)
            for item in fields(authorization_decision) if item.name != "decision_fingerprint"
        }
        if isinstance(decision_payload.get("reason_codes"), tuple):
            decision_payload["reason_codes"] = list(decision_payload["reason_codes"])
        flags["authorization_decision_verified"] = (
            _hash_json(decision_payload) == getattr(authorization_decision, "decision_fingerprint", None)
        )
        if not flags["authorization_request_verified"] or not flags["authorization_decision_verified"]:
            return reject("AUTHORIZATION_CONTRACT_INVALID")

        auth_ok = all((
            getattr(authorization_decision, "authorized", None) is True,
            getattr(authorization_decision, "status", None) == "authorized_not_executed",
            getattr(authorization_decision, "authorization_consumed", None) is False,
            getattr(authorization_decision, "authorization_reusable", None) is False,
            getattr(authorization_decision, "authorization_id", None) == request.authorization_id,
            getattr(authorization_request, "request_fingerprint", None) == request.authorization_request_fingerprint,
            getattr(authorization_decision, "decision_fingerprint", None) == request.authorization_decision_fingerprint,
            getattr(authorization_decision, "authorized_execution_plan_fingerprint", None) == request.execution_plan_fingerprint,
            getattr(authorization_decision, "authorized_adapter_index", None) == request.selected_adapter_index,
            getattr(authorization_decision, "authorized_unit_count", None) == 1,
            getattr(authorization_decision, "authorized_provider_request_limit", None) == 1,
            getattr(authorization_decision, "authorized_translation_request_limit", None) == 1,
            getattr(authorization_decision, "authorized_retry_limit", None) == 0,
            getattr(authorization_decision, "authorized_fallback_limit", None) == 0,
            getattr(authorization_decision, "output_replacement_authorized", None) is False,
            getattr(authorization_decision, "production_integration_authorized", None) is False,
        ))
        flags["authorization_binding_verified"] = auth_ok
        if not auth_ok:
            return reject("AUTHORIZATION_NOT_ELIGIBLE")

        flags["stage62_request_verified"] = (
            getattr(stage62_request, "request_fingerprint", None) == request.stage62_request_fingerprint
            and _hash_json(json.loads(stage62_request.to_json())) == request.stage62_request_fingerprint
        )
        verification = verify_consumption_record(
            stage62_record,
            request_fingerprint=request.stage62_request_fingerprint,
            authorization_id=request.authorization_id,
            authorization_request_fingerprint=request.authorization_request_fingerprint,
            authorization_decision_fingerprint=request.authorization_decision_fingerprint,
            execution_plan_fingerprint=request.execution_plan_fingerprint,
            adapter_index=request.selected_adapter_index,
            unit_count=1,
        )
        expected_stage62_chain = (
            execution_plan.source.execution_package_fingerprint,
            authorization_decision.upstream_authorization_decision_fingerprint,
            execution_plan.source.approval_record_fingerprint,
            execution_plan.source.runtime_submission_package_fingerprint,
            execution_plan.source.runtime_adapter_request_fingerprint,
            execution_plan.source.runtime_adapter_preparation_fingerprint,
            execution_plan.execution_plan_fingerprint,
            authorization_request.request_fingerprint,
            authorization_decision.decision_fingerprint,
            stage62_request.request_fingerprint,
            stage62_record.record_fingerprint,
        )
        flags["stage62_record_verified"] = verification.valid and (
            stage62_record.record_fingerprint == request.stage62_record_fingerprint
            and tuple(stage62_record.upstream_fingerprint_chain) == expected_stage62_chain
        )
        try:
            flags["stage62_result_verified"] = (
                stage62_result.result_fingerprint == _hash_json(json.loads(stage62_result.to_json()))
                and stage62_result.request == stage62_request
                and stage62_result.record == stage62_record
                and stage62_result.status == "consumption_prepared_not_executed"
                and stage62_result.freeze_gate_verified
                and stage62_result.execution_plan_verified
                and stage62_result.authorization_request_verified
                and stage62_result.authorization_decision_verified
            )
        except Exception:
            flags["stage62_result_verified"] = False
        stage62_state_ok = all((
            getattr(stage62_record, "authorization_consumption_prepared", None) is True,
            getattr(stage62_record, "authorization_consumed", None) is False,
            getattr(stage62_record, "authorization_reusable", None) is False,
            getattr(stage62_record, "durable_reuse_prevention_established", None) is False,
            getattr(stage62_record, "persistent_registry_written", None) is False,
            getattr(stage62_record, "execution_started", None) is False,
            getattr(stage62_record, "execution_completed", None) is False,
            getattr(stage62_record, "consumption_id", None) == request.consumption_id,
            getattr(stage62_record, "selected_adapter_index", None) == request.selected_adapter_index,
        ))
        flags["consumption_binding_verified"] = stage62_state_ok
        if not all((flags["stage62_request_verified"], flags["stage62_record_verified"],
                    flags["stage62_result_verified"], stage62_state_ok)):
            return reject("STAGE62_CONTRACT_INVALID")

        if any(getattr(obj, name, False) for obj in (execution_plan, authorization_decision, stage62_record)
               for name in ("runtime_execution_enabled", "provider_execution_enabled",
                            "network_execution_enabled", "translation_execution_enabled",
                            "output_write_enabled", "resume_write_enabled", "cache_write_enabled",
                            "retry_enabled", "fallback_enabled", "production_hook_enabled")):
            return reject("CAPABILITY_ENABLEMENT_REJECTED")

        claim = AtomicAuthorizationConsumptionClaim(
            claim_id=request.claim_id, consumption_id=request.consumption_id,
            authorization_id=request.authorization_id,
            authorization_request_fingerprint=request.authorization_request_fingerprint,
            authorization_decision_fingerprint=request.authorization_decision_fingerprint,
            execution_plan_fingerprint=request.execution_plan_fingerprint,
            stage62_request_fingerprint=request.stage62_request_fingerprint,
            stage62_record_fingerprint=request.stage62_record_fingerprint,
            selected_adapter_index=request.selected_adapter_index, consumed_unit_count=1,
            authorization_consumption_prepared=True, authorization_consumed=True,
            authorization_reusable=False, durable_reuse_prevention_established=True,
            persistent_registry_written=True, execution_started=False, execution_completed=False,
            runtime_execution_enabled=False, provider_execution_enabled=False,
            network_execution_enabled=False, translation_execution_enabled=False,
            output_write_enabled=False, resume_write_enabled=False, cache_write_enabled=False,
            retry_enabled=False, fallback_enabled=False, production_hook_enabled=False,
            claim_state="durably_consumed_not_executed",
            upstream_fingerprint_chain=tuple(stage62_record.upstream_fingerprint_chain) + (request.request_fingerprint,),
            claim_request_fingerprint=request.request_fingerprint,
        )
        if not verify_atomic_consumption_claim(
            claim, request=request, stage62_request=stage62_request, stage62_record=stage62_record,
            authorization_request=authorization_request, authorization_decision=authorization_decision,
            execution_plan=execution_plan,
        ).valid:
            return reject("CLAIM_VERIFICATION_FAILED", "claim_verification_failed")
        try:
            registry.claim(claim)
            flags["registry_schema_verified"] = True
        except AtomicConsumptionAlreadyConsumedError:
            flags["registry_schema_verified"] = True
            existing = registry.read_claim(request.authorization_decision_fingerprint)
            return self._result(request, existing, flags, tuple(findings), "already_consumed",
                                "do_not_reuse_authorization", duplicate=True)
        except AtomicConsumptionRegistryPathError:
            return reject("REGISTRY_PATH_REJECTED", "registry_path_rejected")
        except AtomicConsumptionRegistrySchemaError:
            return reject("REGISTRY_SCHEMA_MISMATCH", "registry_schema_mismatch")
        except AtomicConsumptionRegistryIntegrityError:
            return reject("REGISTRY_INTEGRITY_FAILURE", "registry_integrity_failure")
        except AtomicConsumptionCommitError:
            return reject("ATOMIC_COMMIT_FAILED", "atomic_commit_failed")
        return self._result(request, claim, flags, tuple(findings),
                            "durably_consumed_not_executed", "retain_for_controlled_execution",
                            committed=True)

    claim_authorization = consume

    @staticmethod
    def _result(request, claim, flags, findings, status, action, *, committed=False, duplicate=False):
        return AtomicAuthorizationConsumptionResult(
            request=request, claim=claim, **flags, atomic_claim_committed=committed,
            duplicate_claim_detected=duplicate, policy_findings=findings, status=status,
            recommended_action=action,
        )
