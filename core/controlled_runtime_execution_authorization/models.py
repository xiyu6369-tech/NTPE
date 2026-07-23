from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field


AuthorizationFindingValue = str | int | bool | None


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256_payload(payload: object) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ControlledRuntimeExecutionAuthorizationFinding:
    code: str
    severity: str
    message: str
    field: str
    expected: AuthorizationFindingValue = None
    observed: AuthorizationFindingValue = None


@dataclass(frozen=True)
class ControlledRuntimeExecutionAuthorizationRequest:
    authorization_id: str
    execution_plan_fingerprint: str
    selected_adapter_index: int
    requested_provider_request_limit: int
    requested_translation_request_limit: int
    retry_requested: bool
    fallback_requested: bool
    output_replacement_requested: bool
    runtime_execution_requested: bool
    provider_execution_requested: bool
    network_execution_requested: bool
    translation_execution_requested: bool
    caller_confirmation: bool
    authorization_scope: str
    purpose: str
    schema_name: str
    schema_version: str
    requested_unit_count: int = 1
    requested_adapter_indices: tuple[int, ...] = ()
    requested_plan_step_fingerprints: tuple[str, ...] = ()
    cache_write_requested: bool = False
    resume_write_requested: bool = False
    production_integration_requested: bool = False
    request_fingerprint: str = field(init=False, default="")

    def __post_init__(self) -> None:
        if not isinstance(self.requested_adapter_indices, tuple):
            raise TypeError("requested_adapter_indices must be a tuple")
        if not isinstance(self.requested_plan_step_fingerprints, tuple):
            raise TypeError("requested_plan_step_fingerprints must be a tuple")
        object.__setattr__(
            self,
            "request_fingerprint",
            _sha256_payload(self.fingerprint_payload()),
        )

    def fingerprint_payload(self) -> dict[str, object]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "authorization_id": self.authorization_id,
            "execution_plan_fingerprint": self.execution_plan_fingerprint,
            "selected_adapter_index": self.selected_adapter_index,
            "requested_provider_request_limit": (
                self.requested_provider_request_limit
            ),
            "requested_translation_request_limit": (
                self.requested_translation_request_limit
            ),
            "retry_requested": self.retry_requested,
            "fallback_requested": self.fallback_requested,
            "output_replacement_requested": self.output_replacement_requested,
            "runtime_execution_requested": self.runtime_execution_requested,
            "provider_execution_requested": self.provider_execution_requested,
            "network_execution_requested": self.network_execution_requested,
            "translation_execution_requested": (
                self.translation_execution_requested
            ),
            "caller_confirmation": self.caller_confirmation,
            "authorization_scope": self.authorization_scope,
            "purpose": self.purpose,
            "requested_unit_count": self.requested_unit_count,
            "requested_adapter_indices": list(self.requested_adapter_indices),
            "requested_plan_step_fingerprints": list(
                self.requested_plan_step_fingerprints
            ),
            "cache_write_requested": self.cache_write_requested,
            "resume_write_requested": self.resume_write_requested,
            "production_integration_requested": (
                self.production_integration_requested
            ),
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.fingerprint_payload(), "request_fingerprint": self.request_fingerprint}

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())


@dataclass(frozen=True)
class ControlledRuntimeExecutionAuthorizationDecision:
    authorization_id: str
    authorized: bool
    status: str
    reason_codes: tuple[str, ...]
    execution_package_fingerprint: str
    upstream_authorization_decision_fingerprint: str
    approval_record_fingerprint: str
    runtime_submission_package_fingerprint: str
    runtime_adapter_request_fingerprint: str
    runtime_adapter_preparation_fingerprint: str
    authorization_request_fingerprint: str
    authorized_execution_plan_fingerprint: str
    authorized_adapter_index: int | None
    authorized_unit_count: int
    authorized_provider_request_limit: int
    authorized_translation_request_limit: int
    authorized_retry_limit: int
    authorized_fallback_limit: int
    output_replacement_authorized: bool
    production_integration_authorized: bool
    runtime_execution_enabled: bool
    provider_execution_enabled: bool
    network_execution_enabled: bool
    translation_execution_enabled: bool
    authorization_consumed: bool
    authorization_reusable: bool
    decision_fingerprint: str
    schema_name: str
    schema_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.reason_codes, tuple):
            raise TypeError("reason_codes must be a tuple")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())


@dataclass(frozen=True)
class ControlledRuntimeExecutionAuthorizationResult:
    request: ControlledRuntimeExecutionAuthorizationRequest
    decision: ControlledRuntimeExecutionAuthorizationDecision
    execution_plan_fingerprint_verified: bool
    freeze_gate_verified: bool
    policy_findings: tuple[ControlledRuntimeExecutionAuthorizationFinding, ...]
    status: str
    recommended_action: str
    runtime_invoked: bool
    provider_invoked: bool
    network_invoked: bool
    translation_invoked: bool
    output_written: bool
    resume_written: bool
    cache_written: bool
    retry_used: bool
    fallback_used: bool
    production_hook_invoked: bool
    result_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.policy_findings, tuple):
            raise TypeError("policy_findings must be a tuple")

    def to_dict(self) -> dict[str, object]:
        return {
            "request": self.request.to_dict(),
            "decision": self.decision.to_dict(),
            "execution_plan_fingerprint_verified": (
                self.execution_plan_fingerprint_verified
            ),
            "freeze_gate_verified": self.freeze_gate_verified,
            "policy_findings": [asdict(item) for item in self.policy_findings],
            "status": self.status,
            "recommended_action": self.recommended_action,
            "runtime_invoked": self.runtime_invoked,
            "provider_invoked": self.provider_invoked,
            "network_invoked": self.network_invoked,
            "translation_invoked": self.translation_invoked,
            "output_written": self.output_written,
            "resume_written": self.resume_written,
            "cache_written": self.cache_written,
            "retry_used": self.retry_used,
            "fallback_used": self.fallback_used,
            "production_hook_invoked": self.production_hook_invoked,
            "result_fingerprint": self.result_fingerprint,
        }

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())

