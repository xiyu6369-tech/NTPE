from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from hashlib import sha256
from typing import Any


# ---------------------------------------------------------------------------
# Canonical JSON helpers
# ---------------------------------------------------------------------------

def _to_json_compact(obj: Any) -> str:
    """Deterministic canonical JSON: UTF-8, sorted keys, compact, no NaN, no ASCII escapes."""
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _sha256_hex(obj: Any) -> str:
    return sha256(_to_json_compact(obj).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Consumption Request
# ---------------------------------------------------------------------------

CONSUMPTION_REQUEST_SCHEMA_NAME = (
    "ntpe.controlled_runtime_authorization_consumption_request"
)
CONSUMPTION_REQUEST_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class ControlledRuntimeAuthorizationConsumptionRequest:
    """Immutable single-use consumption preparation request.

    All fingerprints MUST match the supplied authentic objects exactly.
    The consumption_id is caller-supplied, never generated internally.
    """

    consumption_id: str
    authorization_id: str
    authorization_request_fingerprint: str
    authorization_decision_fingerprint: str
    execution_plan_fingerprint: str
    selected_adapter_index: int
    requested_unit_count: int
    consume_for_single_execution: bool
    caller_confirmation: bool
    consumption_scope: str
    purpose: str
    schema_name: str
    schema_version: str
    request_fingerprint: str = field(default="", init=False, compare=True, repr=True)

    def __post_init__(self) -> None:
        # Validate schema name / version immutably
        if self.schema_name != CONSUMPTION_REQUEST_SCHEMA_NAME:
            raise ValueError(
                f"consumption request schema_name must be "
                f"{CONSUMPTION_REQUEST_SCHEMA_NAME!r}, got {self.schema_name!r}"
            )
        if self.schema_version != CONSUMPTION_REQUEST_SCHEMA_VERSION:
            raise ValueError(
                f"consumption request schema_version must be "
                f"{CONSUMPTION_REQUEST_SCHEMA_VERSION!r}, got {self.schema_version!r}"
            )
        # Reject bool as int for policy-sensitive numeric types
        if self.requested_unit_count is True or self.requested_unit_count is False:
            raise TypeError("requested_unit_count must be int, got bool")
        if self.selected_adapter_index is True or self.selected_adapter_index is False:
            raise TypeError("selected_adapter_index must be int, got bool")
        # Reject int as bool
        if isinstance(self.consume_for_single_execution, int) and not isinstance(self.consume_for_single_execution, bool):  # type: ignore[unused-ignore]
            pass  # bool is an int, so the "and not bool" only keeps pure int
        # Actually: check with `not isinstance(x, bool)`
        if isinstance(self.consume_for_single_execution, int) and type(self.consume_for_single_execution) is int:
            raise TypeError("consume_for_single_execution must be bool, got int")
        if isinstance(self.caller_confirmation, int) and type(self.caller_confirmation) is int:
            raise TypeError("caller_confirmation must be bool, got int")
        # Compute fingerprint
        payload = self._fingerprint_payload()
        fingerprint = _sha256_hex(payload)
        object.__setattr__(self, "request_fingerprint", fingerprint)

    def _fingerprint_payload(self) -> dict[str, object]:
        ordered: dict[str, object] = {}
        for f in fields(self):
            if f.name == "request_fingerprint":
                continue
            ordered[f.name] = getattr(self, f.name)
        return ordered

    def to_json(self) -> str:
        return _to_json_compact(self._fingerprint_payload())

    def fingerprint_bytes(self) -> bytes:
        return self.to_json().encode("utf-8")


# ---------------------------------------------------------------------------
# Consumption Record
# ---------------------------------------------------------------------------

CONSUMPTION_RECORD_SCHEMA_NAME = (
    "ntpe.controlled_runtime_authorization_consumption_record"
)
CONSUMPTION_RECORD_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class ControlledRuntimeAuthorizationConsumptionRecord:
    """Immutable consumption preparation record — offline contract only.

    This record represents consumption *preparation*, NOT actual consumption.
    ``authorization_consumed`` remains ``False``.
    """

    consumption_id: str
    authorization_id: str
    authorization_request_fingerprint: str
    authorization_decision_fingerprint: str
    execution_plan_fingerprint: str
    selected_adapter_index: int
    consumed_unit_count: int
    previous_authorization_consumed: bool
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
    status: str
    reason_codes: tuple[str, ...]
    upstream_fingerprint_chain: tuple[str, ...]
    consumption_request_fingerprint: str
    record_fingerprint: str = field(default="", init=False, compare=True, repr=True)
    schema_name: str
    schema_version: str

    def __post_init__(self) -> None:
        if self.schema_name != CONSUMPTION_RECORD_SCHEMA_NAME:
            raise ValueError(
                f"record schema_name must be {CONSUMPTION_RECORD_SCHEMA_NAME!r}, "
                f"got {self.schema_name!r}"
            )
        if self.schema_version != CONSUMPTION_RECORD_SCHEMA_VERSION:
            raise ValueError(
                f"record schema_version must be {CONSUMPTION_RECORD_SCHEMA_VERSION!r}, "
                f"got {self.schema_version!r}"
            )
        # Ensure upstream chain / reason codes are immutable tuples
        if isinstance(self.upstream_fingerprint_chain, list):
            raise TypeError("upstream_fingerprint_chain must be tuple, got list")
        if isinstance(self.reason_codes, list):
            raise TypeError("reason_codes must be tuple, got list")
        # Bool/int safety for numeric fields
        for name in ("consumed_unit_count", "selected_adapter_index"):
            val = getattr(self, name)
            if val is True or val is False:
                raise TypeError(f"{name} must be int, got bool")
        # Compute fingerprint
        payload = self._fingerprint_payload()
        fingerprint = _sha256_hex(payload)
        object.__setattr__(self, "record_fingerprint", fingerprint)

    def _fingerprint_payload(self) -> dict[str, object]:
        ordered: dict[str, object] = {}
        for f in fields(self):
            if f.name == "record_fingerprint":
                continue
            if f.name == "upstream_fingerprint_chain":
                continue  # chain contains self-referential hash — excluded from fingerprint
            value: object = getattr(self, f.name)
            if isinstance(value, tuple):
                value = list(value)  # stable JSON serialisation
            ordered[f.name] = value
        return ordered

    def to_json(self) -> str:
        return _to_json_compact(self._fingerprint_payload())

    def fingerprint_bytes(self) -> bytes:
        return self.to_json().encode("utf-8")


# ---------------------------------------------------------------------------
# Policy Finding
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ControlledRuntimeAuthorizationConsumptionFinding:
    """Immutable policy finding — deterministic, bounded, no stack traces."""

    code: str
    severity: str
    message: str
    field: str
    expected: str
    observed: str

    def _fingerprint_payload(self) -> dict[str, str]:
        o: dict[str, str] = {}
        for f_ in fields(self):
            o[f_.name] = getattr(self, f_.name)
        return o


# ---------------------------------------------------------------------------
# Consumption Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ControlledRuntimeAuthorizationConsumptionResult:
    """Immutable preparation result — no execution, no writes."""

    request: ControlledRuntimeAuthorizationConsumptionRequest
    record: ControlledRuntimeAuthorizationConsumptionRecord
    freeze_gate_verified: bool
    execution_plan_verified: bool
    authorization_request_verified: bool
    authorization_decision_verified: bool
    authorization_binding_verified: bool
    prior_consumption_state_verified: bool
    policy_findings: tuple[ControlledRuntimeAuthorizationConsumptionFinding, ...]
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
    result_fingerprint: str = field(default="", init=False, compare=True, repr=True)

    def __post_init__(self) -> None:
        if not isinstance(self.policy_findings, tuple):
            raise TypeError("policy_findings must be tuple, got list")
        # fingerprint
        payload = self._fingerprint_payload()
        fingerprint = _sha256_hex(payload)
        object.__setattr__(self, "result_fingerprint", fingerprint)

    def _fingerprint_payload(self) -> dict[str, object]:
        ordered: dict[str, object] = {}
        for f in fields(self):
            if f.name == "result_fingerprint":
                continue
            value: object = getattr(self, f.name)
            if f.name == "request":
                # noinspection PyUnresolvedReferences
                ordered[f.name] = json.loads(self.request.to_json())
            elif f.name == "record":
                # noinspection PyUnresolvedReferences
                ordered[f.name] = json.loads(self.record.to_json())
            elif isinstance(value, tuple):
                findings_array: list[object] = []
                for item in value:
                    if isinstance(item, ControlledRuntimeAuthorizationConsumptionFinding):
                        findings_array.append(item._fingerprint_payload())
                    else:
                        findings_array.append(item)
                ordered[f.name] = findings_array
            else:
                ordered[f.name] = value
        return ordered

    def to_json(self) -> str:
        return _to_json_compact(self._fingerprint_payload())


# ---------------------------------------------------------------------------
# Policy (single instance exported)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ControlledRuntimeAuthorizationConsumptionPolicy:
    """Immutable policy constants for Stage 6.2 consumption preparation.

    This policy encodes the exact rules for consumption preparation.
    It does NOT execute, does NOT persist, does NOT authorise execution.
    """

    available_statuses: tuple[str, ...] = (
        "consumption_prepared_not_executed",
        "rejected",
        "invalid_request",
        "authorization_not_eligible",
        "upstream_contract_mismatch",
        "already_consumed",
        "durable_enforcement_unavailable",
    )

    recommendation_action_set: tuple[str, ...] = (
        "retain_for_atomic_execution_boundary",
        "correct_request",
        "reject",
        "rebuild_from_frozen_contract",
        "do_not_reuse_authorization",
        "require_future_durable_consumption_store",
    )

    severity_levels: tuple[str, ...] = ("info", "warning", "error", "blocking")

    allowed_schema_name: str = CONSUMPTION_REQUEST_SCHEMA_NAME
    allowed_request_schema_name: str = CONSUMPTION_REQUEST_SCHEMA_NAME
    allowed_request_schema_version: str = CONSUMPTION_REQUEST_SCHEMA_VERSION
    allowed_record_schema_name: str = CONSUMPTION_RECORD_SCHEMA_NAME
    allowed_record_schema_version: str = CONSUMPTION_RECORD_SCHEMA_VERSION

    max_allowed_findings: int = 200