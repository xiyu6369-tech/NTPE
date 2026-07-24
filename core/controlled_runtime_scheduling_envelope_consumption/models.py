"""Deterministic immutable Stage 6.9 models."""

from __future__ import annotations

from dataclasses import dataclass, field

from .policy import (
    BOUNDARY_KIND,
    CLAIM_SCHEMA_NAME,
    CLAIM_SCHEMA_VERSION,
    REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION,
    RESULT_SCHEMA_NAME,
    RESULT_SCHEMA_VERSION,
    SUCCESS_STATUS,
)
from .serialization import canonical_json, canonical_sha256, model_values

_HEX = frozenset("0123456789abcdef")


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    if len(value) > 256:
        raise ValueError(f"{name} is too long")


def _require_fingerprint(name: str, value: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise ValueError(f"{name} must be lowercase SHA-256 hex")


def _derived_id(prefix: str, payload: object) -> str:
    return f"{prefix}-{canonical_sha256(payload)[:32]}"


@dataclass(frozen=True)
class ControlledRuntimeSchedulingEnvelopeConsumptionRequest:
    scheduling_envelope_id: str
    scheduling_envelope_fingerprint: str
    scheduling_envelope_request_id: str
    scheduling_envelope_request_fingerprint: str
    stage67_consumption_claim_id: str
    stage67_claim_fingerprint: str
    stage66_scheduling_authorization_id: str
    stage66_decision_fingerprint: str
    runtime_boundary_id: str
    runtime_boundary_kind: str
    selected_adapter_index: int
    unit_scope: int
    upstream_fingerprint_chain: tuple[str, ...]
    schema_name: str = REQUEST_SCHEMA_NAME
    schema_version: str = REQUEST_SCHEMA_VERSION
    consumption_request_id: str = field(default="", init=False)
    request_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if self.schema_name != REQUEST_SCHEMA_NAME:
            raise ValueError("invalid Stage 6.9 request schema")
        if self.schema_version != REQUEST_SCHEMA_VERSION:
            raise ValueError("unsupported Stage 6.9 request schema version")
        for name in (
            "scheduling_envelope_id",
            "scheduling_envelope_request_id",
            "stage67_consumption_claim_id",
            "stage66_scheduling_authorization_id",
            "runtime_boundary_id",
        ):
            _require_text(name, getattr(self, name))
        for name in (
            "scheduling_envelope_fingerprint",
            "scheduling_envelope_request_fingerprint",
            "stage67_claim_fingerprint",
            "stage66_decision_fingerprint",
        ):
            _require_fingerprint(name, getattr(self, name))
        if self.runtime_boundary_kind != BOUNDARY_KIND:
            raise ValueError("unsupported runtime boundary kind")
        if type(self.selected_adapter_index) is not int:
            raise TypeError("selected_adapter_index must be int, not bool")
        if self.selected_adapter_index < 0:
            raise ValueError("selected_adapter_index must not be negative")
        if type(self.unit_scope) is not int:
            raise TypeError("unit_scope must be int, not bool")
        if self.unit_scope != 1:
            raise ValueError("unit_scope must be exactly 1")
        if not isinstance(self.upstream_fingerprint_chain, tuple):
            raise TypeError("upstream_fingerprint_chain must be tuple")
        if len(self.upstream_fingerprint_chain) != 23:
            raise ValueError("upstream chain must contain exactly 23 layers")
        for index, value in enumerate(self.upstream_fingerprint_chain):
            _require_fingerprint(f"upstream_fingerprint_chain[{index}]", value)
        identity_payload = model_values(
            self, exclude=("consumption_request_id", "request_fingerprint")
        )
        request_id = _derived_id("stage69-request", identity_payload)
        object.__setattr__(self, "consumption_request_id", request_id)
        object.__setattr__(
            self,
            "request_fingerprint",
            canonical_sha256(
                model_values(self, exclude=("request_fingerprint",))
            ),
        )

    def to_json(self) -> str:
        return canonical_json(model_values(self))


@dataclass(frozen=True)
class ControlledRuntimeSchedulingEnvelopeConsumptionClaim:
    consumption_request_id: str
    consumption_request_fingerprint: str
    scheduling_envelope_id: str
    scheduling_envelope_fingerprint: str
    scheduling_envelope_request_id: str
    scheduling_envelope_request_fingerprint: str
    stage67_consumption_claim_id: str
    stage67_claim_fingerprint: str
    stage66_scheduling_authorization_id: str
    stage66_decision_fingerprint: str
    runtime_boundary_id: str
    runtime_boundary_kind: str
    selected_adapter_index: int
    unit_scope: int
    scheduling_authorization_consumed: bool
    scheduling_envelope_prepared: bool
    scheduling_envelope_consumed: bool
    scheduling_envelope_reusable: bool
    queue_admission_authorized: bool
    runtime_execution_scheduled: bool
    queue_record_created: bool
    execution_started: bool
    persistent_registry_written: bool
    claim_state: str
    canonical_chain: tuple[str, ...]
    schema_name: str = CLAIM_SCHEMA_NAME
    schema_version: str = CLAIM_SCHEMA_VERSION
    consumption_claim_id: str = field(default="", init=False)
    claim_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if self.schema_name != CLAIM_SCHEMA_NAME:
            raise ValueError("invalid Stage 6.9 claim schema")
        if self.schema_version != CLAIM_SCHEMA_VERSION:
            raise ValueError("unsupported Stage 6.9 claim schema version")
        for name in (
            "consumption_request_id",
            "scheduling_envelope_id",
            "scheduling_envelope_request_id",
            "stage67_consumption_claim_id",
            "stage66_scheduling_authorization_id",
            "runtime_boundary_id",
        ):
            _require_text(name, getattr(self, name))
        for name in (
            "consumption_request_fingerprint",
            "scheduling_envelope_fingerprint",
            "scheduling_envelope_request_fingerprint",
            "stage67_claim_fingerprint",
            "stage66_decision_fingerprint",
        ):
            _require_fingerprint(name, getattr(self, name))
        if self.runtime_boundary_kind != BOUNDARY_KIND:
            raise ValueError("unsupported runtime boundary kind")
        if type(self.selected_adapter_index) is not int:
            raise TypeError("selected_adapter_index must be int, not bool")
        if type(self.unit_scope) is not int:
            raise TypeError("unit_scope must be int, not bool")
        if self.unit_scope != 1:
            raise ValueError("unit_scope must be exactly 1")
        expected_flags = {
            "scheduling_authorization_consumed": True,
            "scheduling_envelope_prepared": True,
            "scheduling_envelope_consumed": True,
            "scheduling_envelope_reusable": False,
            "queue_admission_authorized": False,
            "runtime_execution_scheduled": False,
            "queue_record_created": False,
            "execution_started": False,
            "persistent_registry_written": True,
        }
        for name, expected in expected_flags.items():
            value = getattr(self, name)
            if type(value) is not bool:
                raise TypeError(f"{name} must be bool")
            if value is not expected:
                raise ValueError(f"{name} invariant violated")
        if self.claim_state != SUCCESS_STATUS:
            raise ValueError("invalid Stage 6.9 claim state")
        if not isinstance(self.canonical_chain, tuple):
            raise TypeError("canonical_chain must be tuple")
        if len(self.canonical_chain) not in (24, 25):
            raise ValueError("claim chain must have 24 pre-claim or 25 layers")
        for index, value in enumerate(self.canonical_chain):
            _require_fingerprint(f"canonical_chain[{index}]", value)
        pre_claim = self.canonical_chain[:24]
        identity_payload = self._fingerprint_payload(pre_claim)
        claim_id = _derived_id("stage69-claim", identity_payload)
        object.__setattr__(self, "consumption_claim_id", claim_id)
        fingerprint = canonical_sha256(
            self._fingerprint_payload(pre_claim, claim_id=claim_id)
        )
        object.__setattr__(self, "claim_fingerprint", fingerprint)
        object.__setattr__(self, "canonical_chain", pre_claim + (fingerprint,))

    def _fingerprint_payload(
        self,
        chain: tuple[str, ...] | None = None,
        *,
        claim_id: str | None = None,
    ) -> dict[str, object]:
        payload = model_values(
            self,
            exclude=("consumption_claim_id", "claim_fingerprint", "canonical_chain"),
        )
        payload["consumption_claim_id"] = (
            self.consumption_claim_id if claim_id is None else claim_id
        )
        payload["canonical_chain"] = list(
            self.canonical_chain[:24] if chain is None else chain
        )
        return payload

    def to_json(self) -> str:
        return canonical_json(model_values(self))


@dataclass(frozen=True)
class ControlledRuntimeSchedulingEnvelopeConsumptionVerificationResult:
    valid: bool
    schema_verified: bool
    identity_verified: bool
    fingerprint_verified: bool
    envelope_binding_verified: bool
    upstream_binding_verified: bool
    chain_verified: bool
    runtime_boundary_verified: bool
    unit_scope_verified: bool
    state_verified: bool
    persistence_verified: bool
    canonical_payload_verified: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class ControlledRuntimeSchedulingEnvelopeConsumptionResult:
    request: ControlledRuntimeSchedulingEnvelopeConsumptionRequest
    claim: ControlledRuntimeSchedulingEnvelopeConsumptionClaim | None
    verification_succeeded: bool
    upstream_verification_succeeded: bool
    durable_claim_created: bool
    exactly_one_envelope_consumed: bool
    replay_detected: bool
    persistence_committed: bool
    durable_readback_verified: bool
    status: str
    reason_codes: tuple[str, ...]
    schema_name: str = RESULT_SCHEMA_NAME
    schema_version: str = RESULT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_name != RESULT_SCHEMA_NAME:
            raise ValueError("invalid Stage 6.9 result schema")
        if self.schema_version != RESULT_SCHEMA_VERSION:
            raise ValueError("unsupported Stage 6.9 result schema version")
        for name in (
            "verification_succeeded",
            "upstream_verification_succeeded",
            "durable_claim_created",
            "exactly_one_envelope_consumed",
            "replay_detected",
            "persistence_committed",
            "durable_readback_verified",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")
        if not isinstance(self.reason_codes, tuple):
            raise TypeError("reason_codes must be tuple")
