"""Immutable deterministic Stage 6.13 models."""

from __future__ import annotations

from dataclasses import dataclass, field

from .policy import (
    ADMISSION_CLASS,
    BOUNDARY_KIND,
    CLAIM_SCHEMA_NAME,
    CLAIM_SCHEMA_VERSION,
    CONSUMPTION_INTENT,
    PRIORITY_CLASS,
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


def _fp(name: str, value: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(c not in _HEX for c in value):
        raise ValueError(f"{name} must be lowercase SHA-256 hex")


def _text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")


def _id(prefix: str, payload: object) -> str:
    return f"{prefix}-{canonical_sha256(payload)[:32]}"

# ============================================================
# Stage 6.13 Consumption Request
# ============================================================
@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionRecordConsumptionRequest:
    # Stage 6.12 record bindings
    record_id: str
    record_fingerprint: str
    record_request_id: str
    record_request_fingerprint: str
    # Stage 6.11 bindings
    consumption_claim_id: str
    claim_fingerprint: str
    upstream_consumption_request_id: str
    consumption_request_fingerprint: str
    # Stage 6.10 authorization
    authorization_id: str
    decision_fingerprint: str
    authorization_request_id: str
    authorization_request_fingerprint: str
    # Stage 6.9 -> 6.6 chain
    stage69_consumption_claim_id: str
    stage69_claim_fingerprint: str
    scheduling_envelope_id: str
    scheduling_envelope_fingerprint: str
    stage67_consumption_claim_id: str
    stage67_claim_fingerprint: str
    stage66_scheduling_authorization_id: str
    stage66_decision_fingerprint: str
    # Runtime boundary
    runtime_boundary_id: str
    runtime_boundary_kind: str
    selected_adapter_index: int
    capability_state_fingerprint: str
    # Admission metadata
    unit_scope: int
    admission_class: str
    priority_class: str
    ordering_key: str
    # Chain + Identity
    upstream_chain: tuple[str, ...]

    consumption_intent: str = CONSUMPTION_INTENT
    schema_name: str = REQUEST_SCHEMA_NAME
    schema_version: str = REQUEST_SCHEMA_VERSION

    # Computed fields
    consumption_request_id: str = field(default="", init=False)
    request_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            REQUEST_SCHEMA_NAME,
            REQUEST_SCHEMA_VERSION,
        ):
            raise ValueError("invalid Stage 6.13 request schema")
        for name in (
            "record_id",
            "record_request_id",
            "consumption_claim_id",
            "upstream_consumption_request_id",
            "authorization_id",
            "authorization_request_id",
            "stage69_consumption_claim_id",
            "scheduling_envelope_id",
            "stage67_consumption_claim_id",
            "stage66_scheduling_authorization_id",
            "runtime_boundary_id",
            "ordering_key",
        ):
            _text(name, getattr(self, name))
        for name in (
            "record_fingerprint",
            "record_request_fingerprint",
            "claim_fingerprint",
            "consumption_request_fingerprint",
            "decision_fingerprint",
            "authorization_request_fingerprint",
            "stage69_claim_fingerprint",
            "scheduling_envelope_fingerprint",
            "stage67_claim_fingerprint",
            "stage66_decision_fingerprint",
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
        if self.consumption_intent != CONSUMPTION_INTENT:
            raise ValueError("invalid consumption intent")
        if self.admission_class != ADMISSION_CLASS:
            raise ValueError("invalid admission class")
        if self.priority_class != PRIORITY_CLASS:
            raise ValueError("invalid priority class")
        if not isinstance(self.upstream_chain, tuple) or len(self.upstream_chain) != 31:
            raise ValueError("upstream_chain must contain exactly 31 layers")
        for index, value in enumerate(self.upstream_chain):
            _fp(f"upstream_chain[{index}]", value)
        identity = _id(
            "stage613-record-consumption-request",
            values(self, exclude=("consumption_request_id", "request_fingerprint")),
        )
        object.__setattr__(self, "consumption_request_id", identity)
        object.__setattr__(
            self,
            "request_fingerprint",
            canonical_sha256(values(self, exclude=("request_fingerprint",))),
        )

    def to_json(self) -> str:
        from .serialization import canonical_json

        return canonical_json(values(self))

# ============================================================
# Stage 6.13 Durable Consumption Claim
# ============================================================
@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionRecordConsumptionClaim:
    # Request identity
    consumption_request_id: str
    consumption_request_fingerprint: str
    # Stage 6.12 record bindings
    record_id: str
    record_fingerprint: str
    record_request_id: str
    record_request_fingerprint: str
    # Stage 6.11 bindings
    stage611_claim_id: str
    stage611_claim_fingerprint: str
    # Stage 6.10 authorization
    authorization_id: str
    decision_fingerprint: str
    authorization_request_id: str
    authorization_request_fingerprint: str
    # Stage 6.9 -> 6.6 chain
    stage69_consumption_claim_id: str
    stage69_claim_fingerprint: str
    scheduling_envelope_id: str
    scheduling_envelope_fingerprint: str
    stage67_consumption_claim_id: str
    stage67_claim_fingerprint: str
    stage66_scheduling_authorization_id: str
    stage66_decision_fingerprint: str
    # Runtime boundary
    runtime_boundary_id: str
    runtime_boundary_kind: str
    selected_adapter_index: int
    capability_state_fingerprint: str
    # Admission metadata
    unit_scope: int
    admission_class: str
    priority_class: str
    ordering_key: str
    # Inherited scheduling state
    scheduling_authorization_consumed: bool
    scheduling_envelope_prepared: bool
    scheduling_envelope_consumed: bool
    scheduling_envelope_reusable: bool
    # Queue admission state
    queue_admission_authorized: bool
    queue_admission_authorization_consumed: bool
    queue_admission_authorization_reusable: bool
    queue_admission_record_prepared: bool
    queue_admission_record_consumed: bool
    queue_admission_record_reusable: bool
    queue_record_created: bool
    runtime_execution_scheduled: bool
    execution_started: bool
    # Persistence
    persistent_registry_written: bool
    canonical_chain: tuple[str, ...]
    claim_state: str = SUCCESS_STATUS
    schema_name: str = CLAIM_SCHEMA_NAME
    schema_version: str = CLAIM_SCHEMA_VERSION

    # Computed
    consumption_claim_id: str = field(default="", init=False)
    claim_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            CLAIM_SCHEMA_NAME,
            CLAIM_SCHEMA_VERSION,
        ):
            raise ValueError("invalid Stage 6.13 claim schema")
        expected = {
            "scheduling_authorization_consumed": True,
            "scheduling_envelope_prepared": True,
            "scheduling_envelope_consumed": True,
            "scheduling_envelope_reusable": False,
            "queue_admission_authorized": True,
            "queue_admission_authorization_consumed": True,
            "queue_admission_authorization_reusable": False,
            "queue_admission_record_prepared": True,
            "queue_admission_record_consumed": True,
            "queue_admission_record_reusable": False,
            "queue_record_created": False,
            "runtime_execution_scheduled": False,
            "execution_started": False,
            "persistent_registry_written": True,
        }
        for name, required in expected.items():
            if type(getattr(self, name)) is not bool or getattr(self, name) is not required:
                raise ValueError(f"{name} invariant violated")
        if self.claim_state != SUCCESS_STATUS:
            raise ValueError("invalid claim state")
        if type(self.unit_scope) is not int or self.unit_scope != 1:
            raise ValueError("unit_scope must be strict integer 1")
        if self.admission_class != ADMISSION_CLASS:
            raise ValueError("invalid admission class")
        if self.priority_class != PRIORITY_CLASS:
            raise ValueError("invalid priority class")
        if not isinstance(self.canonical_chain, tuple) or len(self.canonical_chain) not in (32, 33):
            raise ValueError("claim chain must have 32 or 33 layers")
        pre = self.canonical_chain[:32]
        identity_payload = self._payload(pre, consumption_claim_id="")
        identity = _id("stage613-record-consumption-claim", identity_payload)
        object.__setattr__(self, "consumption_claim_id", identity)
        fingerprint = canonical_sha256(
            self._payload(pre, consumption_claim_id=identity)
        )
        object.__setattr__(self, "claim_fingerprint", fingerprint)
        object.__setattr__(self, "canonical_chain", pre + (fingerprint,))

    def _payload(
        self, chain: tuple[str, ...], *, consumption_claim_id: str
    ) -> dict[str, object]:
        payload = values(
            self,
            exclude=("consumption_claim_id", "claim_fingerprint", "canonical_chain"),
        )
        payload["consumption_claim_id"] = consumption_claim_id
        payload["canonical_chain"] = list(chain)
        return payload

    def to_json(self) -> str:
        from .serialization import canonical_json

        return canonical_json(values(self))

# ============================================================
# Verification Result
# ============================================================
@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionRecordConsumptionVerificationResult:
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

# ============================================================
# Consumption Result
# ============================================================
@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionRecordConsumptionResult:
    request: ControlledRuntimeQueueAdmissionRecordConsumptionRequest
    claim: ControlledRuntimeQueueAdmissionRecordConsumptionClaim | None
    verification_succeeded: bool
    upstream_verified: bool
    durable_claim_created: bool
    exactly_one_record_consumed: bool
    replay_detected: bool
    persistence_committed: bool
    durable_readback_verified: bool
    status: str
    reason_codes: tuple[str, ...]
    record_consumption_count: int
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
            RESULT_SCHEMA_NAME,
            RESULT_SCHEMA_VERSION,
        ):
            raise ValueError("invalid Stage 6.13 result schema")
        if self.status not in (SUCCESS_STATUS, "queue_admission_record_consumption_failed"):
            raise ValueError("invalid Stage 6.13 result status")