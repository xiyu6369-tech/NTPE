"""Immutable deterministic Stage 6.10 models."""

from __future__ import annotations

from dataclasses import dataclass, field

from .policy import (
    ADMISSION_INTENT, AUTHORIZED_STATUS, BOUNDARY_KIND,
    DECISION_SCHEMA_NAME, DECISION_SCHEMA_VERSION,
    DENIED_STATUS, REQUEST_SCHEMA_NAME, REQUEST_SCHEMA_VERSION,
    RESULT_SCHEMA_NAME, RESULT_SCHEMA_VERSION,
    VERIFICATION_SCHEMA_NAME, VERIFICATION_SCHEMA_VERSION,
)
from .serialization import canonical_sha256, model_values

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
class ControlledRuntimeQueueAdmissionAuthorizationRequest:
    stage69_consumption_claim_id: str
    stage69_claim_fingerprint: str
    stage69_consumption_request_id: str
    stage69_request_fingerprint: str
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
    admission_intent: str = ADMISSION_INTENT
    schema_name: str = REQUEST_SCHEMA_NAME
    schema_version: str = REQUEST_SCHEMA_VERSION
    authorization_request_id: str = field(default="", init=False)
    request_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            REQUEST_SCHEMA_NAME, REQUEST_SCHEMA_VERSION
        ):
            raise ValueError("invalid Stage 6.10 request schema")
        for name in (
            "stage69_consumption_claim_id", "stage69_consumption_request_id",
            "scheduling_envelope_id", "stage67_consumption_claim_id",
            "stage66_scheduling_authorization_id", "runtime_boundary_id",
        ):
            _text(name, getattr(self, name))
        for name in (
            "stage69_claim_fingerprint", "stage69_request_fingerprint",
            "scheduling_envelope_fingerprint", "stage67_claim_fingerprint",
            "stage66_decision_fingerprint", "capability_state_fingerprint",
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
        if self.admission_intent != ADMISSION_INTENT:
            raise ValueError("invalid queue-admission intent")
        if not isinstance(self.upstream_chain, tuple) or len(self.upstream_chain) != 25:
            raise ValueError("upstream_chain must contain exactly 25 layers")
        for index, value in enumerate(self.upstream_chain):
            _fp(f"upstream_chain[{index}]", value)
        identity = _id(
            "stage610-request",
            model_values(self, exclude=("authorization_request_id", "request_fingerprint")),
        )
        object.__setattr__(self, "authorization_request_id", identity)
        object.__setattr__(
            self, "request_fingerprint",
            canonical_sha256(model_values(self, exclude=("request_fingerprint",))),
        )


@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionAuthorizationDecision:
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
    authorization_status: str
    reason_codes: tuple[str, ...]
    scheduling_authorization_consumed: bool
    scheduling_envelope_prepared: bool
    scheduling_envelope_consumed: bool
    scheduling_envelope_reusable: bool
    queue_admission_authorized: bool
    queue_admission_authorization_consumed: bool
    queue_admission_record_prepared: bool
    queue_admission_record_consumed: bool
    queue_record_created: bool
    runtime_execution_scheduled: bool
    execution_started: bool
    canonical_chain: tuple[str, ...]
    schema_name: str = DECISION_SCHEMA_NAME
    schema_version: str = DECISION_SCHEMA_VERSION
    authorization_id: str = field(default="", init=False)
    decision_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            DECISION_SCHEMA_NAME, DECISION_SCHEMA_VERSION
        ):
            raise ValueError("invalid Stage 6.10 decision schema")
        if self.authorization_status != AUTHORIZED_STATUS or self.reason_codes:
            raise ValueError("successful decision must be authorized without reasons")
        if not isinstance(self.reason_codes, tuple):
            raise TypeError("reason_codes must be tuple")
        expected = {
            "scheduling_authorization_consumed": True,
            "scheduling_envelope_prepared": True,
            "scheduling_envelope_consumed": True,
            "scheduling_envelope_reusable": False,
            "queue_admission_authorized": True,
            "queue_admission_authorization_consumed": False,
            "queue_admission_record_prepared": False,
            "queue_admission_record_consumed": False,
            "queue_record_created": False,
            "runtime_execution_scheduled": False,
            "execution_started": False,
        }
        for name, required in expected.items():
            if type(getattr(self, name)) is not bool or getattr(self, name) is not required:
                raise ValueError(f"{name} invariant violated")
        if type(self.unit_scope) is not int or self.unit_scope != 1:
            raise ValueError("unit_scope must be strict integer 1")
        if not isinstance(self.canonical_chain, tuple) or len(self.canonical_chain) not in (26, 27):
            raise ValueError("decision chain must have 26 or 27 layers")
        pre = self.canonical_chain[:26]
        identity_payload = self._payload(pre, authorization_id="")
        identity = _id("stage610-authorization", identity_payload)
        object.__setattr__(self, "authorization_id", identity)
        fingerprint = canonical_sha256(self._payload(pre, authorization_id=identity))
        object.__setattr__(self, "decision_fingerprint", fingerprint)
        object.__setattr__(self, "canonical_chain", pre + (fingerprint,))

    def _payload(self, chain: tuple[str, ...], *, authorization_id: str) -> dict[str, object]:
        payload = model_values(
            self, exclude=("authorization_id", "decision_fingerprint", "canonical_chain")
        )
        payload["authorization_id"] = authorization_id
        payload["canonical_chain"] = list(chain)
        return payload


@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionAuthorizationVerificationResult:
    valid: bool
    schema_verified: bool
    identity_verified: bool
    fingerprint_verified: bool
    upstream_verified: bool
    binding_verified: bool
    chain_verified: bool
    state_verified: bool
    reason_codes: tuple[str, ...]
    schema_name: str = VERIFICATION_SCHEMA_NAME
    schema_version: str = VERIFICATION_SCHEMA_VERSION


@dataclass(frozen=True)
class ControlledRuntimeQueueAdmissionAuthorizationResult:
    request: ControlledRuntimeQueueAdmissionAuthorizationRequest
    decision: ControlledRuntimeQueueAdmissionAuthorizationDecision | None
    authorized: bool
    upstream_verified: bool
    status: str
    reason_codes: tuple[str, ...]
    request_count: int
    decision_count: int
    queue_admission_count: int = 0
    queue_record_count: int = 0
    scheduler_access_count: int = 0
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
            raise ValueError("invalid Stage 6.10 result schema")
        if self.status not in (AUTHORIZED_STATUS, DENIED_STATUS):
            raise ValueError("invalid Stage 6.10 result status")
