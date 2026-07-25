"""Immutable deterministic Stage 7.1 queue-admission models."""

from __future__ import annotations

from dataclasses import dataclass, field

from .policy import (
    ADMISSION_CLASS,
    ADMISSION_INTENT,
    BOUNDARY_KIND,
    FAILURE_STATUS,
    PRIORITY_CLASS,
    QUEUE_RECORD_SCHEMA_NAME,
    QUEUE_RECORD_SCHEMA_VERSION,
    QUEUE_STATE,
    REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION,
    RESULT_SCHEMA_NAME,
    RESULT_SCHEMA_VERSION,
    SUCCESS_STATUS,
    VERIFICATION_SCHEMA_NAME,
    VERIFICATION_SCHEMA_VERSION,
)
from .serialization import canonical_sha256, values

_HEX = frozenset("0123456789abcdef")


def _fingerprint(name: str, value: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise ValueError(f"{name} must be lowercase SHA-256 hex")


def _text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")


def _identity(prefix: str, payload: object) -> str:
    return f"{prefix}-{canonical_sha256(payload)[:32]}"


_id = _identity


@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionRequest:
    stage613_claim_id: str
    stage613_claim_fingerprint: str
    stage613_consumption_request_id: str
    stage613_consumption_request_fingerprint: str
    stage612_record_id: str
    stage612_record_fingerprint: str
    stage612_preparation_request_id: str
    stage612_request_fingerprint: str
    stage611_claim_id: str
    stage611_claim_fingerprint: str
    stage610_authorization_id: str
    stage610_decision_fingerprint: str
    stage610_authorization_request_id: str
    stage610_request_fingerprint: str
    stage69_consumption_claim_id: str
    stage69_claim_fingerprint: str
    stage68_scheduling_envelope_id: str
    stage68_envelope_fingerprint: str
    stage67_consumption_claim_id: str
    stage67_claim_fingerprint: str
    stage66_scheduling_authorization_id: str
    stage66_decision_fingerprint: str
    runtime_boundary_id: str
    runtime_boundary_kind: str
    selected_adapter_index: int
    capability_state_fingerprint: str
    admission_class: str
    priority_class: str
    ordering_key: str
    unit_scope: int
    upstream_chain: tuple[str, ...]
    admission_intent: str = ADMISSION_INTENT
    schema_name: str = REQUEST_SCHEMA_NAME
    schema_version: str = REQUEST_SCHEMA_VERSION
    admission_request_id: str = field(default="", init=False)
    request_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            REQUEST_SCHEMA_NAME,
            REQUEST_SCHEMA_VERSION,
        ):
            raise ValueError("invalid Stage 7.1 admission-request schema")
        for name in (
            "stage613_claim_id",
            "stage613_consumption_request_id",
            "stage612_record_id",
            "stage612_preparation_request_id",
            "stage611_claim_id",
            "stage610_authorization_id",
            "stage610_authorization_request_id",
            "stage69_consumption_claim_id",
            "stage68_scheduling_envelope_id",
            "stage67_consumption_claim_id",
            "stage66_scheduling_authorization_id",
            "runtime_boundary_id",
            "ordering_key",
        ):
            _text(name, getattr(self, name))
        for name in (
            "stage613_claim_fingerprint",
            "stage613_consumption_request_fingerprint",
            "stage612_record_fingerprint",
            "stage612_request_fingerprint",
            "stage611_claim_fingerprint",
            "stage610_decision_fingerprint",
            "stage610_request_fingerprint",
            "stage69_claim_fingerprint",
            "stage68_envelope_fingerprint",
            "stage67_claim_fingerprint",
            "stage66_decision_fingerprint",
            "capability_state_fingerprint",
        ):
            _fingerprint(name, getattr(self, name))
        if self.runtime_boundary_kind != BOUNDARY_KIND:
            raise ValueError("invalid runtime-boundary kind")
        if (
            type(self.selected_adapter_index) is not int
            or self.selected_adapter_index < 0
        ):
            raise TypeError("selected_adapter_index must be a non-negative int")
        if type(self.unit_scope) is not int:
            raise TypeError("unit_scope must be int, not bool")
        if self.unit_scope != 1:
            raise ValueError("unit_scope must be exactly 1")
        if self.admission_class != ADMISSION_CLASS:
            raise ValueError("invalid admission class")
        if self.priority_class != PRIORITY_CLASS:
            raise ValueError("invalid priority class")
        if self.admission_intent != ADMISSION_INTENT:
            raise ValueError("invalid admission intent")
        if (
            not isinstance(self.upstream_chain, tuple)
            or len(self.upstream_chain) != 33
        ):
            raise ValueError("upstream_chain must contain exactly 33 layers")
        for index, item in enumerate(self.upstream_chain):
            _fingerprint(f"upstream_chain[{index}]", item)
        if len(set(self.upstream_chain)) != 33:
            raise ValueError("upstream_chain layers must be unique")
        if self.upstream_chain[-1] != self.stage613_claim_fingerprint:
            raise ValueError("Stage 6.13 terminal fingerprint mismatch")
        identity = _identity(
            "stage71-queue-admission-request",
            values(
                self,
                exclude=("admission_request_id", "request_fingerprint"),
            ),
        )
        object.__setattr__(self, "admission_request_id", identity)
        object.__setattr__(
            self,
            "request_fingerprint",
            canonical_sha256(values(self, exclude=("request_fingerprint",))),
        )

    def to_json(self) -> str:
        from .serialization import canonical_json

        return canonical_json(values(self))


@dataclass(frozen=True)
class ControlledRuntimeQueueRecord:
    admission_request_id: str
    admission_request_fingerprint: str
    stage613_claim_id: str
    stage613_claim_fingerprint: str
    stage613_consumption_request_id: str
    stage613_consumption_request_fingerprint: str
    stage612_record_id: str
    stage612_record_fingerprint: str
    stage612_preparation_request_id: str
    stage612_request_fingerprint: str
    stage611_claim_id: str
    stage611_claim_fingerprint: str
    stage610_authorization_id: str
    stage610_decision_fingerprint: str
    stage610_authorization_request_id: str
    stage610_request_fingerprint: str
    stage69_consumption_claim_id: str
    stage69_claim_fingerprint: str
    stage68_scheduling_envelope_id: str
    stage68_envelope_fingerprint: str
    stage67_consumption_claim_id: str
    stage67_claim_fingerprint: str
    stage66_scheduling_authorization_id: str
    stage66_decision_fingerprint: str
    runtime_boundary_id: str
    runtime_boundary_kind: str
    selected_adapter_index: int
    capability_state_fingerprint: str
    admission_class: str
    priority_class: str
    ordering_key: str
    unit_scope: int
    scheduling_authorization_consumed: bool
    scheduling_envelope_prepared: bool
    scheduling_envelope_consumed: bool
    scheduling_envelope_reusable: bool
    queue_admission_authorized: bool
    queue_admission_authorization_consumed: bool
    queue_admission_record_prepared: bool
    queue_admission_record_consumed: bool
    queue_admission_performed: bool
    queue_record_created: bool
    queue_record_consumed: bool
    queue_record_reusable: bool
    runtime_execution_scheduled: bool
    execution_started: bool
    persistent_registry_written: bool
    queue_state: str
    canonical_chain: tuple[str, ...]
    schema_name: str = QUEUE_RECORD_SCHEMA_NAME
    schema_version: str = QUEUE_RECORD_SCHEMA_VERSION
    queue_record_id: str = field(default="", init=False)
    queue_record_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            QUEUE_RECORD_SCHEMA_NAME,
            QUEUE_RECORD_SCHEMA_VERSION,
        ):
            raise ValueError("invalid Stage 7.1 queue-record schema")
        for name in (
            "admission_request_id",
            "stage613_claim_id",
            "stage613_consumption_request_id",
            "stage612_record_id",
            "stage612_preparation_request_id",
            "stage611_claim_id",
            "stage610_authorization_id",
            "stage610_authorization_request_id",
            "stage69_consumption_claim_id",
            "stage68_scheduling_envelope_id",
            "stage67_consumption_claim_id",
            "stage66_scheduling_authorization_id",
            "runtime_boundary_id",
            "ordering_key",
        ):
            _text(name, getattr(self, name))
        for name in (
            "admission_request_fingerprint",
            "stage613_claim_fingerprint",
            "stage613_consumption_request_fingerprint",
            "stage612_record_fingerprint",
            "stage612_request_fingerprint",
            "stage611_claim_fingerprint",
            "stage610_decision_fingerprint",
            "stage610_request_fingerprint",
            "stage69_claim_fingerprint",
            "stage68_envelope_fingerprint",
            "stage67_claim_fingerprint",
            "stage66_decision_fingerprint",
            "capability_state_fingerprint",
        ):
            _fingerprint(name, getattr(self, name))
        if self.runtime_boundary_kind != BOUNDARY_KIND:
            raise ValueError("invalid runtime-boundary kind")
        if (
            type(self.selected_adapter_index) is not int
            or self.selected_adapter_index < 0
        ):
            raise TypeError("selected_adapter_index must be a non-negative int")
        if type(self.unit_scope) is not int or self.unit_scope != 1:
            raise ValueError("unit_scope must be strict integer 1")
        if self.admission_class != ADMISSION_CLASS:
            raise ValueError("invalid admission class")
        if self.priority_class != PRIORITY_CLASS:
            raise ValueError("invalid priority class")
        if self.queue_state != QUEUE_STATE:
            raise ValueError("invalid immutable queue state")
        expected = {
            "scheduling_authorization_consumed": True,
            "scheduling_envelope_prepared": True,
            "scheduling_envelope_consumed": True,
            "scheduling_envelope_reusable": False,
            "queue_admission_authorized": True,
            "queue_admission_authorization_consumed": True,
            "queue_admission_record_prepared": True,
            "queue_admission_record_consumed": True,
            "queue_admission_performed": True,
            "queue_record_created": True,
            "queue_record_consumed": False,
            "queue_record_reusable": False,
            "runtime_execution_scheduled": False,
            "execution_started": False,
            "persistent_registry_written": True,
        }
        for name, required in expected.items():
            if (
                type(getattr(self, name)) is not bool
                or getattr(self, name) is not required
            ):
                raise ValueError(f"{name} invariant violated")
        if (
            not isinstance(self.canonical_chain, tuple)
            or len(self.canonical_chain) not in (34, 35)
        ):
            raise ValueError("queue-record chain must have 34 or 35 layers")
        pre_chain = self.canonical_chain[:34]
        for index, item in enumerate(pre_chain):
            _fingerprint(f"canonical_chain[{index}]", item)
        if len(set(pre_chain)) != 34:
            raise ValueError("queue-record chain layers must be unique")
        if pre_chain[-1] != self.admission_request_fingerprint:
            raise ValueError("admission-request layer is not terminal pre-record")
        identity = _identity(
            "stage71-runtime-queue-record",
            self._payload(pre_chain, queue_record_id=""),
        )
        object.__setattr__(self, "queue_record_id", identity)
        fingerprint = canonical_sha256(
            self._payload(pre_chain, queue_record_id=identity)
        )
        object.__setattr__(self, "queue_record_fingerprint", fingerprint)
        object.__setattr__(
            self,
            "canonical_chain",
            pre_chain + (fingerprint,),
        )

    def _payload(
        self,
        chain: tuple[str, ...],
        *,
        queue_record_id: str,
    ) -> dict[str, object]:
        payload = values(
            self,
            exclude=(
                "queue_record_id",
                "queue_record_fingerprint",
                "canonical_chain",
            ),
        )
        payload["queue_record_id"] = queue_record_id
        payload["canonical_chain"] = list(chain)
        return payload

    def to_json(self) -> str:
        from .serialization import canonical_json

        return canonical_json(values(self))


@dataclass(frozen=True)
class ControlledRuntimeQueueRecordVerificationResult:
    valid: bool
    schema_verified: bool
    identity_verified: bool
    fingerprint_verified: bool
    upstream_verified: bool
    binding_verified: bool
    intent_verified: bool
    chain_verified: bool
    state_verified: bool
    persistence_verified: bool
    durable_readback_verified: bool
    canonical_payload_verified: bool
    reason_codes: tuple[str, ...]
    schema_name: str = VERIFICATION_SCHEMA_NAME
    schema_version: str = VERIFICATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            VERIFICATION_SCHEMA_NAME,
            VERIFICATION_SCHEMA_VERSION,
        ):
            raise ValueError("invalid Stage 7.1 verification-result schema")
        for name in (
            "valid",
            "schema_verified",
            "identity_verified",
            "fingerprint_verified",
            "upstream_verified",
            "binding_verified",
            "intent_verified",
            "chain_verified",
            "state_verified",
            "persistence_verified",
            "durable_readback_verified",
            "canonical_payload_verified",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")
        if not isinstance(self.reason_codes, tuple):
            raise TypeError("reason_codes must be an immutable tuple")


@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionResult:
    request: ControlledRuntimeQueueAdmissionRequest
    queue_record: ControlledRuntimeQueueRecord | None
    verification_succeeded: bool
    upstream_verified: bool
    queue_admission_performed: bool
    queue_record_created: bool
    replay_detected: bool
    conflict_detected: bool
    persistence_committed: bool
    durable_readback_verified: bool
    status: str
    reason_codes: tuple[str, ...]
    queue_admission_count: int
    queue_record_created_count: int
    queue_record_consumed_count: int = 0
    runtime_schedule_count: int = 0
    scheduler_count: int = 0
    task_created_count: int = 0
    job_created_count: int = 0
    worker_created_count: int = 0
    runtime_execution_count: int = 0
    provider_execution_count: int = 0
    network_execution_count: int = 0
    translation_execution_count: int = 0
    output_write_count: int = 0
    resume_write_count: int = 0
    cache_write_count: int = 0
    schema_name: str = RESULT_SCHEMA_NAME
    schema_version: str = RESULT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            RESULT_SCHEMA_NAME,
            RESULT_SCHEMA_VERSION,
        ):
            raise ValueError("invalid Stage 7.1 admission-result schema")
        if self.status not in (SUCCESS_STATUS, FAILURE_STATUS):
            raise ValueError("invalid Stage 7.1 admission-result status")
        if not isinstance(self.request, ControlledRuntimeQueueAdmissionRequest):
            raise TypeError("request must be a Stage 7.1 admission request")
        for name in (
            "verification_succeeded",
            "upstream_verified",
            "queue_admission_performed",
            "queue_record_created",
            "replay_detected",
            "conflict_detected",
            "persistence_committed",
            "durable_readback_verified",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")
        if not isinstance(self.reason_codes, tuple):
            raise TypeError("reason_codes must be an immutable tuple")
        count_names = (
            "queue_admission_count",
            "queue_record_created_count",
            "queue_record_consumed_count",
            "runtime_schedule_count",
            "scheduler_count",
            "task_created_count",
            "job_created_count",
            "worker_created_count",
            "runtime_execution_count",
            "provider_execution_count",
            "network_execution_count",
            "translation_execution_count",
            "output_write_count",
            "resume_write_count",
            "cache_write_count",
        )
        if any(
            type(getattr(self, name)) is not int or getattr(self, name) < 0
            for name in count_names
        ):
            raise ValueError("result counts must be non-negative integers")
        if self.status == SUCCESS_STATUS:
            if not all(
                (
                    isinstance(self.queue_record, ControlledRuntimeQueueRecord),
                    self.verification_succeeded,
                    self.upstream_verified,
                    self.queue_admission_performed,
                    self.queue_record_created,
                    not self.replay_detected,
                    not self.conflict_detected,
                    self.persistence_committed,
                    self.durable_readback_verified,
                    self.queue_admission_count == 1,
                    self.queue_record_created_count == 1,
                    not self.reason_codes,
                )
            ):
                raise ValueError("success-result invariant violated")
