"""Immutable canonical models for Stage 6.3."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, fields
from hashlib import sha256
from typing import Any

REQUEST_SCHEMA_NAME = "ntpe.controlled_runtime_atomic_authorization_consumption_claim_request"
REQUEST_SCHEMA_VERSION = "1.0"
CLAIM_SCHEMA_NAME = "ntpe.controlled_runtime_atomic_authorization_consumption_claim"
CLAIM_SCHEMA_VERSION = "1.0"
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}\Z")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def canonical_sha256(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _values(instance: object, *, exclude: tuple[str, ...] = ()) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in fields(instance):
        if item.name in exclude:
            continue
        value = getattr(instance, item.name)
        if isinstance(value, tuple):
            value = list(value)
        result[item.name] = value
    return result


@dataclass(frozen=True)
class AtomicAuthorizationConsumptionClaimRequest:
    claim_id: str
    consumption_id: str
    authorization_id: str
    authorization_request_fingerprint: str
    authorization_decision_fingerprint: str
    execution_plan_fingerprint: str
    stage62_request_fingerprint: str
    stage62_record_fingerprint: str
    selected_adapter_index: int
    requested_unit_count: int
    claim_for_single_execution: bool
    caller_confirmation: bool
    registry_scope: str
    purpose: str
    schema_name: str = REQUEST_SCHEMA_NAME
    schema_version: str = REQUEST_SCHEMA_VERSION
    request_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if self.schema_name != REQUEST_SCHEMA_NAME or self.schema_version != REQUEST_SCHEMA_VERSION:
            raise ValueError("unsupported atomic claim request schema")
        if not isinstance(self.claim_id, str) or not _ID_RE.fullmatch(self.claim_id):
            raise ValueError("claim_id must be caller-supplied, non-empty, bounded, and structurally valid")
        if not isinstance(self.consumption_id, str) or not _ID_RE.fullmatch(self.consumption_id):
            raise ValueError("consumption_id must be non-empty, bounded, and structurally valid")
        if type(self.selected_adapter_index) is not int:
            raise TypeError("selected_adapter_index must be int, not bool")
        if type(self.requested_unit_count) is not int:
            raise TypeError("requested_unit_count must be int, not bool")
        if type(self.claim_for_single_execution) is not bool:
            raise TypeError("claim_for_single_execution must be bool")
        if type(self.caller_confirmation) is not bool:
            raise TypeError("caller_confirmation must be bool")
        if not isinstance(self.registry_scope, str) or not self.registry_scope:
            raise ValueError("registry_scope must be explicit")
        for name in (
            "authorization_id", "authorization_request_fingerprint",
            "authorization_decision_fingerprint", "execution_plan_fingerprint",
            "stage62_request_fingerprint", "stage62_record_fingerprint",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        object.__setattr__(self, "request_fingerprint", canonical_sha256(self._fingerprint_payload()))

    def _fingerprint_payload(self) -> dict[str, Any]:
        return _values(self, exclude=("request_fingerprint",))

    def to_json(self) -> str:
        return canonical_json(self._fingerprint_payload())


@dataclass(frozen=True)
class AtomicAuthorizationConsumptionClaim:
    claim_id: str
    consumption_id: str
    authorization_id: str
    authorization_request_fingerprint: str
    authorization_decision_fingerprint: str
    execution_plan_fingerprint: str
    stage62_request_fingerprint: str
    stage62_record_fingerprint: str
    selected_adapter_index: int
    consumed_unit_count: int
    authorization_consumption_prepared: bool
    authorization_consumed: bool
    authorization_reusable: bool
    durable_reuse_prevention_established: bool
    persistent_registry_written: bool
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
    claim_state: str
    upstream_fingerprint_chain: tuple[str, ...]
    claim_request_fingerprint: str
    claim_fingerprint: str = field(default="", init=False)
    schema_name: str = CLAIM_SCHEMA_NAME
    schema_version: str = CLAIM_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_name != CLAIM_SCHEMA_NAME or self.schema_version != CLAIM_SCHEMA_VERSION:
            raise ValueError("unsupported atomic claim schema")
        if not isinstance(self.upstream_fingerprint_chain, tuple):
            raise TypeError("upstream_fingerprint_chain must be tuple")
        if type(self.selected_adapter_index) is not int or type(self.consumed_unit_count) is not int:
            raise TypeError("claim numeric fields must be int, not bool")
        upstream = self.upstream_fingerprint_chain
        if len(upstream) == 13:
            upstream = upstream[:-1]
        if len(upstream) != 12:
            raise ValueError("claim requires the first twelve layers of the fingerprint chain")
        fingerprint = canonical_sha256(self._fingerprint_payload(upstream))
        object.__setattr__(self, "claim_fingerprint", fingerprint)
        object.__setattr__(self, "upstream_fingerprint_chain", tuple(upstream) + (fingerprint,))

    def _fingerprint_payload(self, upstream: tuple[str, ...] | None = None) -> dict[str, Any]:
        payload = _values(self, exclude=("claim_fingerprint", "upstream_fingerprint_chain"))
        chain = upstream if upstream is not None else self.upstream_fingerprint_chain[:12]
        payload["upstream_fingerprint_chain"] = list(chain)
        return payload

    def to_json(self) -> str:
        return canonical_json(_values(self))


@dataclass(frozen=True)
class AtomicAuthorizationConsumptionFinding:
    code: str
    severity: str
    message: str
    field: str = ""
    expected: str = ""
    observed: str = ""


@dataclass(frozen=True)
class AtomicAuthorizationConsumptionResult:
    request: AtomicAuthorizationConsumptionClaimRequest
    claim: AtomicAuthorizationConsumptionClaim | None
    freeze_gate_verified: bool
    execution_plan_verified: bool
    authorization_request_verified: bool
    authorization_decision_verified: bool
    stage62_request_verified: bool
    stage62_record_verified: bool
    stage62_result_verified: bool
    authorization_binding_verified: bool
    consumption_binding_verified: bool
    registry_path_verified: bool
    registry_schema_verified: bool
    atomic_claim_committed: bool
    duplicate_claim_detected: bool
    policy_findings: tuple[AtomicAuthorizationConsumptionFinding, ...]
    status: str
    recommended_action: str
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
        object.__setattr__(self, "result_fingerprint", canonical_sha256(self._fingerprint_payload()))

    def _fingerprint_payload(self) -> dict[str, Any]:
        payload = _values(self, exclude=("result_fingerprint", "request", "claim", "policy_findings"))
        payload["request"] = json.loads(self.request.to_json())
        payload["request"]["request_fingerprint"] = self.request.request_fingerprint
        payload["claim"] = json.loads(self.claim.to_json()) if self.claim else None
        payload["policy_findings"] = [_values(item) for item in self.policy_findings]
        return payload

    def to_json(self) -> str:
        return canonical_json(self._fingerprint_payload())
