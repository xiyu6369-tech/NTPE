"""Deterministic immutable models for the Stage 6.5 handoff boundary."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, fields
from typing import Any

REQUEST_SCHEMA_NAME = "ntpe.controlled_runtime_handoff_request"
REQUEST_SCHEMA_VERSION = "1.0"
RECEIPT_SCHEMA_NAME = "ntpe.controlled_runtime_handoff_receipt"
RECEIPT_SCHEMA_VERSION = "1.0"

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_UUID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_HEX = re.compile(r"^[0-9a-f]{64}$")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
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
        raise ValueError(f"{name} must be caller supplied, not a generated UUID")
    if not _ID.fullmatch(value):
        raise ValueError(f"{name} is malformed or exceeds 128 characters")


@dataclass(frozen=True)
class ControlledRuntimeHandoffRequest:
    handoff_id: str
    envelope_id: str
    claim_id: str
    consumption_id: str
    authorization_id: str
    execution_plan_fingerprint: str
    authorization_decision_fingerprint: str
    stage63_claim_fingerprint: str
    stage64_envelope_request_fingerprint: str
    stage64_envelope_fingerprint: str
    selected_adapter_index: int
    requested_unit_count: int
    runtime_boundary_id: str
    runtime_boundary_kind: str
    handoff_requested: bool
    caller_confirmation: bool
    scheduling_requested: bool
    execution_requested: bool
    provider_requested: bool
    translation_requested: bool
    handoff_scope: str
    purpose: str
    schema_name: str = REQUEST_SCHEMA_NAME
    schema_version: str = REQUEST_SCHEMA_VERSION
    request_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if self.schema_name != REQUEST_SCHEMA_NAME:
            raise ValueError("invalid handoff request schema")
        if self.schema_version != REQUEST_SCHEMA_VERSION:
            raise ValueError("unsupported handoff request version")
        _require_id("handoff_id", self.handoff_id, reject_uuid=True)
        for name in ("envelope_id", "claim_id", "consumption_id", "authorization_id"):
            _require_id(name, getattr(self, name))
        _require_id("runtime_boundary_id", self.runtime_boundary_id)
        for name in (
            "execution_plan_fingerprint", "authorization_decision_fingerprint",
            "stage63_claim_fingerprint", "stage64_envelope_request_fingerprint",
            "stage64_envelope_fingerprint",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not _HEX.fullmatch(value):
                raise ValueError(f"{name} must be lowercase SHA-256 hex")
        if type(self.selected_adapter_index) is not int:
            raise TypeError("selected_adapter_index must be int, not bool")
        if type(self.requested_unit_count) is not int:
            raise TypeError("requested_unit_count must be int, not bool")
        if self.requested_unit_count != 1:
            raise ValueError("requested_unit_count must be exactly 1")
        for name in (
            "handoff_requested", "caller_confirmation", "scheduling_requested",
            "execution_requested", "provider_requested", "translation_requested",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")
        if self.handoff_requested is not True or self.caller_confirmation is not True:
            raise ValueError("handoff_requested and caller_confirmation must be true")
        if any((
            self.scheduling_requested, self.execution_requested,
            self.provider_requested, self.translation_requested,
        )):
            raise ValueError("scheduling, execution, Provider, and Translation requests must be false")
        if self.runtime_boundary_kind != "controlled_offline_acceptance_boundary":
            raise ValueError("unsupported runtime boundary kind")
        if not isinstance(self.handoff_scope, str) or not self.handoff_scope:
            raise ValueError("handoff_scope must be explicit")
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
class ControlledRuntimeHandoffReceipt:
    handoff_id: str
    envelope_id: str
    claim_id: str
    consumption_id: str
    authorization_id: str
    execution_plan_fingerprint: str
    authorization_decision_fingerprint: str
    stage63_claim_fingerprint: str
    stage64_envelope_request_fingerprint: str
    stage64_envelope_fingerprint: str
    selected_adapter_index: int
    accepted_unit_count: int
    runtime_boundary_id: str
    runtime_boundary_kind: str
    authorization_consumed: bool
    authorization_reusable: bool
    durable_reuse_prevention_established: bool
    persistent_registry_written: bool
    runtime_handoff_prepared: bool
    runtime_handoff_completed: bool
    runtime_boundary_accepted: bool
    runtime_execution_scheduled: bool
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
    receipt_state: str
    upstream_fingerprint_chain: tuple[str, ...]
    handoff_request_fingerprint: str
    receipt_fingerprint: str = field(default="", init=False)
    schema_name: str = RECEIPT_SCHEMA_NAME
    schema_version: str = RECEIPT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.upstream_fingerprint_chain, tuple):
            raise TypeError("upstream_fingerprint_chain must be tuple")
        pre_receipt = self.upstream_fingerprint_chain[:16]
        fingerprint = canonical_sha256(self._fingerprint_payload(pre_receipt))
        object.__setattr__(self, "receipt_fingerprint", fingerprint)
        object.__setattr__(
            self, "upstream_fingerprint_chain", tuple(pre_receipt) + (fingerprint,),
        )

    def _fingerprint_payload(
        self, upstream: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        payload = _values(
            self, exclude=("receipt_fingerprint", "upstream_fingerprint_chain"),
        )
        payload["upstream_fingerprint_chain"] = list(
            self.upstream_fingerprint_chain[:16] if upstream is None else upstream
        )
        return payload

    def to_json(self) -> str:
        return canonical_json(_values(self))


@dataclass(frozen=True)
class ControlledRuntimeHandoffFinding:
    code: str
    severity: str
    message: str
    field: str = ""
    expected: str = ""
    observed: str = ""


@dataclass(frozen=True)
class ControlledRuntimeHandoffResult:
    request: ControlledRuntimeHandoffRequest
    receipt: ControlledRuntimeHandoffReceipt | None
    freeze_gate_verified: bool
    execution_plan_verified: bool
    authorization_verified: bool
    stage62_verified: bool
    stage63_claim_verified: bool
    stage64_envelope_request_verified: bool
    stage64_envelope_verified: bool
    stage64_result_verified: bool
    authorization_binding_verified: bool
    claim_binding_verified: bool
    envelope_binding_verified: bool
    adapter_index_verified: bool
    execution_unit_verified: bool
    runtime_boundary_verified: bool
    handoff_scope_verified: bool
    policy_findings: tuple[ControlledRuntimeHandoffFinding, ...]
    status: str
    recommended_action: str
    runtime_boundary_invoked: bool
    runtime_scheduled: bool = False
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
class _RuntimeHandoffVerificationResult:
    valid: bool
    schema_verified: bool
    fingerprint_verified: bool
    request_binding_verified: bool
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
