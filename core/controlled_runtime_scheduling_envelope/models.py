"""Deterministic immutable Stage 6.8 models."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, fields
from typing import Any

REQUEST_SCHEMA_NAME = "ntpe.controlled_runtime_scheduling_envelope_request"
REQUEST_SCHEMA_VERSION = "1.0"
ENVELOPE_SCHEMA_NAME = "ntpe.controlled_runtime_scheduling_envelope"
ENVELOPE_SCHEMA_VERSION = "1.0"

_ID_CHARACTERS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"
)
_HEX_CHARACTERS = frozenset("0123456789abcdef")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
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


def _is_uuid(value: str) -> bool:
    if len(value) != 36 or any(value[index] != "-" for index in (8, 13, 18, 23)):
        return False
    compact = value.replace("-", "").lower()
    return len(compact) == 32 and all(
        character in _HEX_CHARACTERS for character in compact
    )


def _require_id(name: str, value: str, *, reject_uuid: bool = False) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be str")
    if not value.strip():
        raise ValueError(f"{name} must not be blank")
    if reject_uuid and _is_uuid(value):
        raise ValueError(f"{name} must be caller supplied, not a UUID")
    if (
        len(value) > 128
        or not value[0].isalnum()
        or any(character not in _ID_CHARACTERS for character in value)
    ):
        raise ValueError(f"{name} is malformed or exceeds 128 characters")


def _require_fingerprint(name: str, value: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _HEX_CHARACTERS for character in value)
    ):
        raise ValueError(f"{name} must be lowercase SHA-256 hex")


@dataclass(frozen=True)
class ControlledRuntimeSchedulingEnvelopeRequest:
    scheduling_envelope_id: str
    scheduling_consumption_id: str
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
    stage65_handoff_receipt_fingerprint: str
    stage66_scheduling_request_fingerprint: str
    stage66_scheduling_decision_fingerprint: str
    stage67_scheduling_consumption_request_fingerprint: str
    stage67_scheduling_consumption_claim_fingerprint: str
    selected_adapter_index: int
    requested_schedule_unit_count: int
    runtime_boundary_id: str
    runtime_boundary_kind: str
    prepare_scheduling_envelope: bool
    caller_confirmation: bool
    queue_admission_requested: bool
    queue_write_requested: bool
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
            raise ValueError("invalid scheduling-envelope request schema")
        if self.schema_version != REQUEST_SCHEMA_VERSION:
            raise ValueError("unsupported scheduling-envelope request version")
        _require_id(
            "scheduling_envelope_id",
            self.scheduling_envelope_id,
            reject_uuid=True,
        )
        for name in (
            "scheduling_consumption_id",
            "scheduling_authorization_id",
            "handoff_id",
            "envelope_id",
            "claim_id",
            "consumption_id",
            "authorization_id",
            "runtime_boundary_id",
        ):
            _require_id(name, getattr(self, name))
        for name in (
            "execution_plan_fingerprint",
            "execution_authorization_decision_fingerprint",
            "stage63_claim_fingerprint",
            "stage64_envelope_fingerprint",
            "stage65_handoff_receipt_fingerprint",
            "stage66_scheduling_request_fingerprint",
            "stage66_scheduling_decision_fingerprint",
            "stage67_scheduling_consumption_request_fingerprint",
            "stage67_scheduling_consumption_claim_fingerprint",
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
            "prepare_scheduling_envelope",
            "caller_confirmation",
            "queue_admission_requested",
            "queue_write_requested",
            "job_creation_requested",
            "worker_start_requested",
            "runtime_execution_requested",
            "provider_execution_requested",
            "translation_execution_requested",
        )
        for name in boolean_fields:
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")
        if not self.prepare_scheduling_envelope or not self.caller_confirmation:
            raise ValueError("prepare flag and caller confirmation must be true")
        if any(
            (
                self.queue_admission_requested,
                self.queue_write_requested,
                self.job_creation_requested,
                self.worker_start_requested,
                self.runtime_execution_requested,
                self.provider_execution_requested,
                self.translation_execution_requested,
            )
        ):
            raise ValueError("Stage 6.8 cannot request admission or execution")
        if self.runtime_boundary_kind != "controlled_offline_acceptance_boundary":
            raise ValueError("unsupported runtime boundary kind")
        if not isinstance(self.scheduling_scope, str) or not self.scheduling_scope:
            raise ValueError("scheduling_scope must be explicit")
        if not isinstance(self.purpose, str):
            raise TypeError("purpose must be str metadata")
        object.__setattr__(
            self,
            "request_fingerprint",
            canonical_sha256(self._fingerprint_payload()),
        )

    def _fingerprint_payload(self) -> dict[str, Any]:
        return _values(self, exclude=("request_fingerprint",))

    def to_json(self) -> str:
        return canonical_json(_values(self))


@dataclass(frozen=True)
class ControlledRuntimeSchedulingEnvelope:
    scheduling_envelope_id: str
    scheduling_consumption_id: str
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
    stage65_handoff_receipt_fingerprint: str
    stage66_scheduling_request_fingerprint: str
    stage66_scheduling_decision_fingerprint: str
    stage67_scheduling_consumption_request_fingerprint: str
    stage67_scheduling_consumption_claim_fingerprint: str
    selected_adapter_index: int
    schedule_unit_count: int
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
    durable_scheduling_reuse_prevention_established: bool
    persistent_scheduling_registry_written: bool
    scheduling_envelope_prepared: bool
    scheduling_envelope_consumed: bool
    scheduling_envelope_reusable: bool
    queue_admission_authorized: bool
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
    envelope_state: str
    upstream_fingerprint_chain: tuple[str, ...]
    scheduling_envelope_request_fingerprint: str
    scheduling_envelope_fingerprint: str = field(default="", init=False)
    schema_name: str = ENVELOPE_SCHEMA_NAME
    schema_version: str = ENVELOPE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_name != ENVELOPE_SCHEMA_NAME:
            raise ValueError("invalid scheduling-envelope schema")
        if self.schema_version != ENVELOPE_SCHEMA_VERSION:
            raise ValueError("unsupported scheduling-envelope version")
        for name in (
            "scheduling_envelope_id",
            "scheduling_consumption_id",
            "scheduling_authorization_id",
            "handoff_id",
            "envelope_id",
            "claim_id",
            "consumption_id",
            "authorization_id",
            "runtime_boundary_id",
        ):
            _require_id(name, getattr(self, name))
        for name in (
            "execution_plan_fingerprint",
            "execution_authorization_decision_fingerprint",
            "stage63_claim_fingerprint",
            "stage64_envelope_fingerprint",
            "stage65_handoff_receipt_fingerprint",
            "stage66_scheduling_request_fingerprint",
            "stage66_scheduling_decision_fingerprint",
            "stage67_scheduling_consumption_request_fingerprint",
            "stage67_scheduling_consumption_claim_fingerprint",
            "scheduling_envelope_request_fingerprint",
        ):
            _require_fingerprint(name, getattr(self, name))
        if type(self.selected_adapter_index) is not int:
            raise TypeError("selected_adapter_index must be int, not bool")
        if type(self.schedule_unit_count) is not int:
            raise TypeError("schedule_unit_count must be int, not bool")
        if self.schedule_unit_count != 1:
            raise ValueError("schedule_unit_count must be exactly 1")
        if not isinstance(self.upstream_fingerprint_chain, tuple):
            raise TypeError("upstream_fingerprint_chain must be tuple")
        if len(self.upstream_fingerprint_chain) not in (22, 23):
            raise ValueError("envelope chain must have 22 pre-envelope or 23 layers")
        for index, fingerprint in enumerate(
            self.upstream_fingerprint_chain[:22], start=1
        ):
            _require_fingerprint(
                f"upstream_fingerprint_chain[{index}]", fingerprint
            )
        for name in (
            "authorization_consumed",
            "authorization_reusable",
            "durable_reuse_prevention_established",
            "persistent_registry_written",
            "runtime_handoff_prepared",
            "runtime_handoff_completed",
            "runtime_boundary_accepted",
            "scheduling_authorization_requested",
            "scheduling_authorized",
            "scheduling_authorization_consumed",
            "scheduling_authorization_reusable",
            "schedule_once",
            "durable_scheduling_reuse_prevention_established",
            "persistent_scheduling_registry_written",
            "scheduling_envelope_prepared",
            "scheduling_envelope_consumed",
            "scheduling_envelope_reusable",
            "queue_admission_authorized",
            "runtime_execution_scheduled",
            "queue_record_created",
            "job_record_created",
            "worker_started",
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
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")
        if self.envelope_state != (
            "scheduling_envelope_prepared_not_admitted_not_scheduled"
        ):
            raise ValueError("invalid Stage 6.8 envelope_state")
        required_true = (
            self.authorization_consumed,
            self.durable_reuse_prevention_established,
            self.persistent_registry_written,
            self.runtime_handoff_prepared,
            self.runtime_handoff_completed,
            self.runtime_boundary_accepted,
            self.scheduling_authorization_requested,
            self.scheduling_authorized,
            self.scheduling_authorization_consumed,
            self.schedule_once,
            self.durable_scheduling_reuse_prevention_established,
            self.persistent_scheduling_registry_written,
            self.scheduling_envelope_prepared,
        )
        if not all(required_true):
            raise ValueError("required Stage 6.8 state must remain true")
        required_false = (
            self.authorization_reusable,
            self.scheduling_authorization_reusable,
            self.scheduling_envelope_consumed,
            self.scheduling_envelope_reusable,
            self.queue_admission_authorized,
            self.runtime_execution_scheduled,
            self.queue_record_created,
            self.job_record_created,
            self.worker_started,
            self.execution_started,
            self.execution_completed,
            self.runtime_execution_enabled,
            self.provider_execution_enabled,
            self.network_execution_enabled,
            self.translation_execution_enabled,
            self.output_write_enabled,
            self.resume_write_enabled,
            self.cache_write_enabled,
            self.retry_enabled,
            self.fallback_enabled,
            self.production_hook_enabled,
        )
        if any(required_false):
            raise ValueError("forbidden Stage 6.8 state must remain false")
        pre_envelope = self.upstream_fingerprint_chain[:22]
        fingerprint = canonical_sha256(
            self._fingerprint_payload(tuple(pre_envelope))
        )
        object.__setattr__(
            self,
            "scheduling_envelope_fingerprint",
            fingerprint,
        )
        object.__setattr__(
            self,
            "upstream_fingerprint_chain",
            tuple(pre_envelope) + (fingerprint,),
        )

    def _fingerprint_payload(
        self,
        upstream: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        payload = _values(
            self,
            exclude=(
                "scheduling_envelope_fingerprint",
                "upstream_fingerprint_chain",
            ),
        )
        payload["upstream_fingerprint_chain"] = list(
            self.upstream_fingerprint_chain[:22]
            if upstream is None
            else upstream
        )
        return payload

    def to_json(self) -> str:
        return canonical_json(_values(self))


@dataclass(frozen=True)
class ControlledRuntimeSchedulingEnvelopeFinding:
    code: str
    severity: str
    message: str
    field: str = ""


@dataclass(frozen=True)
class ControlledRuntimeSchedulingEnvelopeResult:
    request: ControlledRuntimeSchedulingEnvelopeRequest
    scheduling_envelope: ControlledRuntimeSchedulingEnvelope | None
    freeze_gate_verified: bool
    execution_plan_verified: bool
    execution_authorization_verified: bool
    stage62_verified: bool
    stage63_claim_verified: bool
    stage64_envelope_verified: bool
    stage65_handoff_receipt_verified: bool
    stage66_scheduling_request_verified: bool
    stage66_scheduling_decision_verified: bool
    stage66_result_verified: bool
    stage67_scheduling_consumption_request_verified: bool
    stage67_scheduling_consumption_claim_verified: bool
    stage67_result_verified: bool
    authorization_binding_verified: bool
    claim_binding_verified: bool
    execution_envelope_binding_verified: bool
    handoff_binding_verified: bool
    scheduling_authorization_binding_verified: bool
    scheduling_consumption_binding_verified: bool
    adapter_index_verified: bool
    schedule_unit_verified: bool
    runtime_boundary_verified: bool
    scheduling_scope_verified: bool
    policy_findings: tuple[ControlledRuntimeSchedulingEnvelopeFinding, ...]
    status: str
    recommended_action: str
    builder_invoked: bool
    stage67_registry_read: bool = False
    stage67_registry_written: bool = False
    scheduler_invoked: bool = False
    queue_admission_invoked: bool = False
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
            self,
            "result_fingerprint",
            canonical_sha256(self._fingerprint_payload()),
        )

    def _fingerprint_payload(self) -> dict[str, Any]:
        return _values(self, exclude=("result_fingerprint",))

    def to_json(self) -> str:
        return canonical_json(_values(self))


@dataclass(frozen=True)
class _ControlledRuntimeSchedulingEnvelopeVerificationResult:
    valid: bool
    schema_verified: bool
    fingerprint_verified: bool
    request_binding_verified: bool
    stage67_binding_verified: bool
    stage66_binding_verified: bool
    stage65_binding_verified: bool
    stage64_binding_verified: bool
    stage63_binding_verified: bool
    stage62_binding_verified: bool
    stage61_binding_verified: bool
    plan_binding_verified: bool
    adapter_index_verified: bool
    unit_count_verified: bool
    runtime_boundary_verified: bool
    upstream_chain_verified: bool
    state_verified: bool
    capabilities_disabled: bool
    reason_codes: tuple[str, ...]
