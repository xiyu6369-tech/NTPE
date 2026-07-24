"""Immutable deterministic Stage 6.12 models."""

from __future__ import annotations

from dataclasses import dataclass, field

from .policy import (
    ADMISSION_CLASS, BOUNDARY_KIND, PREPARATION_INTENT,
    PRIORITY_CLASS, RECORD_SCHEMA_NAME, RECORD_SCHEMA_VERSION,
    REQUEST_SCHEMA_NAME, REQUEST_SCHEMA_VERSION,
    RESULT_SCHEMA_NAME, RESULT_SCHEMA_VERSION,
    SUCCESS_STATUS,
    VERIFICATION_SCHEMA_NAME, VERIFICATION_SCHEMA_VERSION,
)
from .serialization import canonical_sha256, values

_HEX = frozenset("0123456789abcdef")


def _fp(name: str, value: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(c not in _HEX for c in value):
        raise ValueError(f"{name} must be lowercase SHA-256 hex")


def _text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")


def _id(prefix: str, payload: object) -> str:
    return f"{prefix}-{canonical_sha256(payload)[:32]}"


@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionRecordRequest:
    consumption_claim_id: str
    claim_fingerprint: str
    consumption_request_id: str
    consumption_request_fingerprint: str
    authorization_id: str
    decision_fingerprint: str
    authorization_request_id: str
    authorization_request_fingerprint: str
    stage69_consumption_claim_id: str
    stage69_claim_fingerprint: str
    scheduling_envelope_id: str
    scheduling_envelope_fingerprint: str
    stage67_consumption_claim_id: str
    stage67_claim_fingerprint: str
    stage66_scheduling_authorization_id: str
    stage66_decision_fingerprint: str
    runtime_boundary_id: str
    runtime_boundary_kind: str
    selected_adapter_index: int
    capability_state_fingerprint: str
    unit_scope: int
    upstream_chain: tuple[str, ...]
    preparation_intent: str = PREPARATION_INTENT
    schema_name: str = REQUEST_SCHEMA_NAME
    schema_version: str = REQUEST_SCHEMA_VERSION
    admission_class: str = ADMISSION_CLASS
    priority_class: str = PRIORITY_CLASS
    record_request_id: str = field(default="", init=False)
    request_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            REQUEST_SCHEMA_NAME, REQUEST_SCHEMA_VERSION
        ):
            raise ValueError("invalid Stage 6.12 request schema")
        for name in (
            "consumption_claim_id", "consumption_request_id",
            "authorization_id", "authorization_request_id",
            "stage69_consumption_claim_id", "scheduling_envelope_id",
            "stage67_consumption_claim_id", "stage66_scheduling_authorization_id",
            "runtime_boundary_id",
        ):
            _text(name, getattr(self, name))
        for name in (
            "claim_fingerprint", "consumption_request_fingerprint",
            "decision_fingerprint", "authorization_request_fingerprint",
            "stage69_claim_fingerprint", "scheduling_envelope_fingerprint",
            "stage67_claim_fingerprint", "stage66_decision_fingerprint",
            "capability_state_fingerprint",
        ):
            _fp(name, getattr(self, name))
        if self.runtime_boundary_kind != BOUNDARY_KIND:
            raise ValueError("invalid runtime boundary kind")
        if type(self.selected_adapter_index) is not int or self.selected_adapter_index < 0:
            raise TypeError("selected_adapter_index must be non-negative int")
        if type(self.unit_scope) is not int:
            raise TypeError("unit_scope must be int, not bool")
        if self.unit_scope != 1:
            raise ValueError("unit_scope must be exactly 1")
        if self.preparation_intent != PREPARATION_INTENT:
            raise ValueError("invalid preparation intent")
        if self.admission_class != ADMISSION_CLASS:
            raise ValueError("invalid admission class")
        if self.priority_class != PRIORITY_CLASS:
            raise ValueError("invalid priority class")
        if not isinstance(self.upstream_chain, tuple) or len(self.upstream_chain) != 29:
            raise ValueError("upstream_chain must contain exactly 29 layers")
        for index, value in enumerate(self.upstream_chain):
            _fp(f"upstream_chain[{index}]", value)
        identity = _id(
            "stage612-record-request",
            values(self, exclude=("record_request_id", "request_fingerprint")),
        )
        object.__setattr__(self, "record_request_id", identity)
        object.__setattr__(
            self, "request_fingerprint",
            canonical_sha256(values(self, exclude=("request_fingerprint",))),
        )


@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionRecord:
    record_request_id: str
    record_request_fingerprint: str
    consumption_claim_id: str
    claim_fingerprint: str
    consumption_request_id: str
    consumption_request_fingerprint: str
    authorization_id: str
    decision_fingerprint: str
    authorization_request_id: str
    authorization_request_fingerprint: str
    stage69_consumption_claim_id: str
    stage69_claim_fingerprint: str
    scheduling_envelope_id: str
    scheduling_envelope_fingerprint: str
    stage67_consumption_claim_id: str
    stage67_claim_fingerprint: str
    stage66_scheduling_authorization_id: str
    stage66_decision_fingerprint: str
    runtime_boundary_id: str
    runtime_boundary_kind: str
    selected_adapter_index: int
    capability_state_fingerprint: str
    unit_scope: int
    admission_class: str
    priority_class: str
    scheduling_authorization_consumed: bool
    scheduling_envelope_prepared: bool
    scheduling_envelope_consumed: bool
    scheduling_envelope_reusable: bool
    queue_admission_authorized: bool
    queue_admission_authorization_consumed: bool
    queue_admission_authorization_reusable: bool
    queue_admission_record_prepared: bool
    queue_admission_record_consumed: bool
    queue_record_created: bool
    runtime_execution_scheduled: bool
    execution_started: bool
    persistent_registry_written: bool
    canonical_chain: tuple[str, ...]
    record_state: str = SUCCESS_STATUS
    schema_name: str = RECORD_SCHEMA_NAME
    schema_version: str = RECORD_SCHEMA_VERSION
    queue_admission_record_id: str = field(default="", init=False)
    record_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            RECORD_SCHEMA_NAME, RECORD_SCHEMA_VERSION
        ):
            raise ValueError("invalid Stage 6.12 record schema")
        expected = {
            "scheduling_authorization_consumed": True,
            "scheduling_envelope_prepared": True,
            "scheduling_envelope_consumed": True,
            "scheduling_envelope_reusable": False,
            "queue_admission_authorized": True,
            "queue_admission_authorization_consumed": True,
            "queue_admission_authorization_reusable": False,
            "queue_admission_record_prepared": True,
            "queue_admission_record_consumed": False,
            "queue_record_created": False,
            "runtime_execution_scheduled": False,
            "execution_started": False,
            "persistent_registry_written": True,
        }
        for name, required in expected.items():
            if type(getattr(self, name)) is not bool or getattr(self, name) is not required:
                raise ValueError(f"{name} invariant violated")
        if self.record_state != SUCCESS_STATUS:
            raise ValueError("invalid record state")
        if type(self.unit_scope) is not int or self.unit_scope != 1:
            raise ValueError("unit_scope must be strict integer 1")
        if self.admission_class != ADMISSION_CLASS:
            raise ValueError("invalid admission class")
        if self.priority_class != PRIORITY_CLASS:
            raise ValueError("invalid priority class")
        if not isinstance(self.canonical_chain, tuple) or len(self.canonical_chain) not in (30, 31):
            raise ValueError("record chain must have 30 or 31 layers")
        pre = self.canonical_chain[:30]
        identity_payload = self._payload(pre, queue_admission_record_id="")
        identity = _id("stage612-record", identity_payload)
        object.__setattr__(self, "queue_admission_record_id", identity)
        fingerprint = canonical_sha256(self._payload(pre, queue_admission_record_id=identity))
        object.__setattr__(self, "record_fingerprint", fingerprint)
        object.__setattr__(self, "canonical_chain", pre + (fingerprint,))

    def _payload(self, chain: tuple[str, ...], *, queue_admission_record_id: str) -> dict[str, object]:
        payload = values(
            self, exclude=(
                "queue_admission_record_id", "record_fingerprint", "canonical_chain"
            )
        )
        payload["queue_admission_record_id"] = queue_admission_record_id
        payload["canonical_chain"] = list(chain)
        return payload


@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionRecordVerificationResult:
    valid: bool
    schema_verified: bool
    identity_verified: bool
    fingerprint_verified: bool
    upstream_verified: bool
    binding_verified: bool
    chain_verified: bool
    state_verified: bool
    persistence_verified: bool
    canonical_payload_verified: bool
    reason_codes: tuple[str, ...]
    schema_name: str = VERIFICATION_SCHEMA_NAME
    schema_version: str = VERIFICATION_SCHEMA_VERSION


@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionRecordResult:
    request: ControlledRuntimeQueueAdmissionRecordRequest
    record: ControlledRuntimeQueueAdmissionRecord | None
    verification_succeeded: bool
    upstream_verified: bool
    durable_record_created: bool
    exactly_one_record_prepared: bool
    replay_detected: bool
    persistence_committed: bool
    durable_readback_verified: bool
    status: str
    reason_codes: tuple[str, ...]
    record_preparation_count: int
    queue_admission_count: int = 0
    queue_record_created_count: int = 0
    queue_record_consumed_count: int = 0
    scheduling_queued_count: int = 0
    scheduler_count: int = 0
    runtime_execution_count: int = 0
    provider_execution_count: int = 0
    network_execution_count: int = 0
    translation_execution_count: int = 0
    schema_name: str = RESULT_SCHEMA_NAME
    schema_version: str = RESULT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            RESULT_SCHEMA_NAME, RESULT_SCHEMA_VERSION
        ):
            raise ValueError("invalid Stage 6.12 result schema")
        if self.status not in (SUCCESS_STATUS, "queue_admission_record_preparation_failed"):
            raise ValueError("invalid Stage 6.12 result status")
