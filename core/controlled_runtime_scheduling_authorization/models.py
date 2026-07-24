"""Deterministic immutable Stage 6.6 models."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, fields
from typing import Any

REQUEST_SCHEMA_NAME = "ntpe.controlled_runtime_scheduling_authorization_request"
REQUEST_SCHEMA_VERSION = "1.0"
DECISION_SCHEMA_NAME = "ntpe.controlled_runtime_scheduling_authorization_decision"
DECISION_SCHEMA_VERSION = "1.0"

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_UUID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_HEX = re.compile(r"^[0-9a-f]{64}$")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    )


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _values(instance: Any, *, exclude: tuple[str, ...] = ()) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in fields(instance):
        if item.name in exclude:
            continue
        value = getattr(instance, item.name)
        if isinstance(value, tuple):
            value = [
                _values(entry) if hasattr(entry, "__dataclass_fields__") else entry
                for entry in value
            ]
        elif hasattr(value, "__dataclass_fields__"):
            value = _values(value)
        result[item.name] = value
    return result


def _require_id(name: str, value: str, *, reject_uuid: bool = False) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be str")
    if not value.strip():
        raise ValueError(f"{name} must not be blank")
    if reject_uuid and _UUID.fullmatch(value):
        raise ValueError(f"{name} must be caller supplied, not a UUID")
    if not _ID.fullmatch(value):
        raise ValueError(f"{name} is malformed or exceeds 128 characters")


def _require_fingerprint(name: str, value: str) -> None:
    if not isinstance(value, str) or not _HEX.fullmatch(value):
        raise ValueError(f"{name} must be lowercase SHA-256 hex")


@dataclass(frozen=True)
class ControlledRuntimeSchedulingAuthorizationRequest:
    scheduling_authorization_id: str
    handoff_id: str
    envelope_id: str
    claim_id: str
    consumption_id: str
    authorization_id: str
    execution_plan_fingerprint: str
    execution_authorization_decision_fingerprint: str
    stage63_claim_fingerprint: str
    stage64_envelope_fingerprint: str
    stage65_handoff_request_fingerprint: str
    stage65_handoff_receipt_fingerprint: str
    selected_adapter_index: int
    requested_schedule_unit_count: int
    runtime_boundary_id: str
    runtime_boundary_kind: str
    scheduling_authorization_requested: bool
    schedule_once: bool
    caller_confirmation: bool
    queue_creation_requested: bool
    job_creation_requested: bool
    worker_start_requested: bool
    runtime_execution_requested: bool
    provider_execution_requested: bool
    translation_execution_requested: bool
    scheduling_scope: str
    purpose: str
    schema_name: str = REQUEST_SCHEMA_NAME
    schema_version: str = REQUEST_SCHEMA_VERSION
    request_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if self.schema_name != REQUEST_SCHEMA_NAME:
            raise ValueError("invalid scheduling authorization request schema")
        if self.schema_version != REQUEST_SCHEMA_VERSION:
            raise ValueError("unsupported scheduling authorization request version")
        _require_id(
            "scheduling_authorization_id", self.scheduling_authorization_id,
            reject_uuid=True,
        )
        for name in (
            "handoff_id", "envelope_id", "claim_id", "consumption_id",
            "authorization_id", "runtime_boundary_id",
        ):
            _require_id(name, getattr(self, name))
        for name in (
            "execution_plan_fingerprint",
            "execution_authorization_decision_fingerprint",
            "stage63_claim_fingerprint", "stage64_envelope_fingerprint",
            "stage65_handoff_request_fingerprint",
            "stage65_handoff_receipt_fingerprint",
        ):
            _require_fingerprint(name, getattr(self, name))
        if type(self.selected_adapter_index) is not int:
            raise TypeError("selected_adapter_index must be int, not bool")
        if self.selected_adapter_index < 0:
            raise ValueError("selected_adapter_index must not be negative")
        if type(self.requested_schedule_unit_count) is not int:
            raise TypeError("requested_schedule_unit_count must be int, not bool")
        if self.requested_schedule_unit_count != 1:
            raise ValueError("requested_schedule_unit_count must be exactly 1")
        boolean_fields = (
            "scheduling_authorization_requested", "schedule_once",
            "caller_confirmation", "queue_creation_requested",
            "job_creation_requested", "worker_start_requested",
            "runtime_execution_requested", "provider_execution_requested",
            "translation_execution_requested",
        )
        for name in boolean_fields:
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")
        if not all((
            self.scheduling_authorization_requested,
            self.schedule_once,
            self.caller_confirmation,
        )):
            raise ValueError(
                "authorization request, schedule_once, and confirmation must be true"
            )
        if any((
            self.queue_creation_requested, self.job_creation_requested,
            self.worker_start_requested, self.runtime_execution_requested,
            self.provider_execution_requested,
            self.translation_execution_requested,
        )):
            raise ValueError("Stage 6.6 cannot request scheduling or execution")
        if self.runtime_boundary_kind != "controlled_offline_acceptance_boundary":
            raise ValueError("unsupported runtime boundary kind")
        if not isinstance(self.scheduling_scope, str) or not self.scheduling_scope:
            raise ValueError("scheduling_scope must be explicit")
        if not isinstance(self.purpose, str):
            raise TypeError("purpose must be str metadata")
        object.__setattr__(
            self, "request_fingerprint",
            canonical_sha256(self._fingerprint_payload()),
        )

    def _fingerprint_payload(self) -> dict[str, Any]:
        return _values(self, exclude=("request_fingerprint",))

    def to_json(self) -> str:
        return canonical_json(_values(self))


@dataclass(frozen=True)
class ControlledRuntimeSchedulingAuthorizationDecision:
    scheduling_authorization_id: str
    handoff_id: str
    envelope_id: str
    claim_id: str
    consumption_id: str
    authorization_id: str
    execution_plan_fingerprint: str
    execution_authorization_decision_fingerprint: str
    stage63_claim_fingerprint: str
    stage64_envelope_fingerprint: str
    stage65_handoff_request_fingerprint: str
    stage65_handoff_receipt_fingerprint: str
    selected_adapter_index: int
    authorized_schedule_unit_count: int
    runtime_boundary_id: str
    runtime_boundary_kind: str
    authorization_consumed: bool
    authorization_reusable: bool
    durable_reuse_prevention_established: bool
    persistent_registry_written: bool
    runtime_handoff_prepared: bool
    runtime_handoff_completed: bool
    runtime_boundary_accepted: bool
    scheduling_authorization_requested: bool
    scheduling_authorized: bool
    scheduling_authorization_consumed: bool
    scheduling_authorization_reusable: bool
    schedule_once: bool
    runtime_execution_scheduled: bool
    queue_record_created: bool
    job_record_created: bool
    worker_started: bool
    execution_started: bool
    execution_completed: bool
    runtime_execution_enabled: bool
    provider_execution_enabled: bool
    network_execution_enabled: bool
    translation_execution_enabled: bool
    output_write_enabled: bool
    resume_write_enabled: bool
    cache_write_enabled: bool
    retry_enabled: bool
    fallback_enabled: bool
    production_hook_enabled: bool
    decision_state: str
    upstream_fingerprint_chain: tuple[str, ...]
    scheduling_authorization_request_fingerprint: str
    decision_fingerprint: str = field(default="", init=False)
    schema_name: str = DECISION_SCHEMA_NAME
    schema_version: str = DECISION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.upstream_fingerprint_chain, tuple):
            raise TypeError("upstream_fingerprint_chain must be tuple")
        pre_decision = self.upstream_fingerprint_chain[:18]
        fingerprint = canonical_sha256(self._fingerprint_payload(pre_decision))
        object.__setattr__(self, "decision_fingerprint", fingerprint)
        object.__setattr__(
            self, "upstream_fingerprint_chain",
            tuple(pre_decision) + (fingerprint,),
        )

    def _fingerprint_payload(
        self, upstream: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        payload = _values(
            self, exclude=("decision_fingerprint", "upstream_fingerprint_chain"),
        )
        payload["upstream_fingerprint_chain"] = list(
            self.upstream_fingerprint_chain[:18] if upstream is None else upstream
        )
        return payload

    def to_json(self) -> str:
        return canonical_json(_values(self))


@dataclass(frozen=True)
class ControlledRuntimeSchedulingAuthorizationFinding:
    code: str
    severity: str
    message: str
    field: str = ""
    expected: str = ""
    observed: str = ""


@dataclass(frozen=True)
class ControlledRuntimeSchedulingAuthorizationResult:
    request: ControlledRuntimeSchedulingAuthorizationRequest
    decision: ControlledRuntimeSchedulingAuthorizationDecision | None
    freeze_gate_verified: bool
    execution_plan_verified: bool
    execution_authorization_verified: bool
    stage62_verified: bool
    stage63_claim_verified: bool
    stage64_envelope_verified: bool
    stage65_handoff_request_verified: bool
    stage65_handoff_receipt_verified: bool
    stage65_result_verified: bool
    authorization_binding_verified: bool
    claim_binding_verified: bool
    envelope_binding_verified: bool
    handoff_binding_verified: bool
    adapter_index_verified: bool
    schedule_unit_verified: bool
    runtime_boundary_verified: bool
    scheduling_scope_verified: bool
    policy_findings: tuple[ControlledRuntimeSchedulingAuthorizationFinding, ...]
    status: str
    recommended_action: str
    authorizer_invoked: bool
    scheduler_invoked: bool = False
    queue_written: bool = False
    job_created: bool = False
    worker_started: bool = False
    runtime_invoked: bool = False
    provider_invoked: bool = False
    network_invoked: bool = False
    translation_invoked: bool = False
    output_written: bool = False
    resume_written: bool = False
    cache_written: bool = False
    retry_used: bool = False
    fallback_used: bool = False
    production_hook_invoked: bool = False
    result_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.policy_findings, tuple):
            raise TypeError("policy_findings must be tuple")
        object.__setattr__(
            self, "result_fingerprint",
            canonical_sha256(self._fingerprint_payload()),
        )

    def _fingerprint_payload(self) -> dict[str, Any]:
        return _values(self, exclude=("result_fingerprint",))

    def to_json(self) -> str:
        return canonical_json(_values(self))


@dataclass(frozen=True)
class _SchedulingAuthorizationDecisionVerificationResult:
    valid: bool
    schema_verified: bool
    fingerprint_verified: bool
    request_binding_verified: bool
    handoff_binding_verified: bool
    envelope_binding_verified: bool
    claim_binding_verified: bool
    stage62_binding_verified: bool
    authorization_binding_verified: bool
    plan_binding_verified: bool
    adapter_index_verified: bool
    unit_count_verified: bool
    runtime_boundary_verified: bool
    upstream_chain_verified: bool
    state_verified: bool
    capabilities_disabled: bool
    reason_codes: tuple[str, ...]
