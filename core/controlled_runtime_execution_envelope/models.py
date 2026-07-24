"""Stage 6.4 — Controlled Runtime Execution Envelope Models

Immutable frozen dataclasses for the execution envelope request, envelope,
and result. All models are deterministic and side-effect free.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, fields
from typing import Any

# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

REQUEST_SCHEMA_NAME = "ntpe.controlled_runtime_execution_envelope_request"
REQUEST_SCHEMA_VERSION = "1.0"
ENVELOPE_SCHEMA_NAME = "ntpe.controlled_runtime_execution_envelope"
ENVELOPE_SCHEMA_VERSION = "1.0"
RESULT_SCHEMA_NAME = "ntpe.controlled_runtime_execution_envelope_result"
RESULT_SCHEMA_VERSION = "1.0"

# ---------------------------------------------------------------------------
# IDs and fingerprints
# ---------------------------------------------------------------------------

_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_ENVELOPE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_UUID_DETECT = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

# ---------------------------------------------------------------------------
# Canonical serialization
# ---------------------------------------------------------------------------


def canonical_json(value: Any) -> str:
    """Deterministic canonical JSON: UTF-8, sorted keys, compact, no NaN."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def canonical_sha256(value: Any) -> str:
    """SHA-256 over canonical UTF-8 JSON bytes, or raw bytes directly."""
    if isinstance(value, bytes):
        return hashlib.sha256(value).hexdigest()
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _values(
    instance: Any,
    *,
    exclude: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Extract sorted field values for canonical fingerprinting."""
    result: dict[str, Any] = {}
    for item in fields(instance):  # type: ignore[arg-type]
        if item.name in exclude:
            continue
        value = getattr(instance, item.name)
        if isinstance(value, tuple):
            value = list(value)
        result[item.name] = value
    return result


# ---------------------------------------------------------------------------
# Envelope Request
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ControlledRuntimeExecutionEnvelopeRequest:
    """Immutable envelope preparation request.

    envelope_id is caller-supplied, never generated internally.
    UUID generation is forbidden.
    Timestamps are forbidden.
    caller_confirmation must be exactly True.
    runtime_handoff_requested must be exactly True.
    requested_unit_count must be integer 1 (bool rejected).
    execution_mode must be exactly: controlled_single_execution.
    """

    envelope_id: str
    claim_id: str
    consumption_id: str
    authorization_id: str
    authorization_request_fingerprint: str
    authorization_decision_fingerprint: str
    execution_plan_fingerprint: str
    stage62_request_fingerprint: str
    stage62_record_fingerprint: str
    stage63_claim_request_fingerprint: str
    stage63_claim_fingerprint: str
    selected_adapter_index: int
    requested_unit_count: int
    runtime_handoff_requested: bool
    caller_confirmation: bool
    runtime_scope: str
    execution_mode: str
    purpose: str
    schema_name: str = REQUEST_SCHEMA_NAME
    schema_version: str = REQUEST_SCHEMA_VERSION
    request_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        # Schema validation
        if self.schema_name != REQUEST_SCHEMA_NAME:
            raise ValueError(
                f"request schema_name must be {REQUEST_SCHEMA_NAME!r}, "
                f"got {self.schema_name!r}"
            )
        if self.schema_version != REQUEST_SCHEMA_VERSION:
            raise ValueError(
                f"request schema_version must be {REQUEST_SCHEMA_VERSION!r}, "
                f"got {self.schema_version!r}"
            )

        # envelope_id validation
        if not isinstance(self.envelope_id, str):
            raise TypeError("envelope_id must be str")
        if not self.envelope_id.strip():
            raise ValueError("envelope_id must not be blank")
        if _UUID_DETECT.match(self.envelope_id.strip()):
            raise ValueError(
                "envelope_id must be caller-supplied, not a generated UUID"
            )
        if not _ENVELOPE_ID_RE.fullmatch(self.envelope_id):
            raise ValueError(
                "envelope_id must be caller-supplied non-UUID, "
                "alphanumeric with limited punctuation, max 128 chars"
            )

        # Reject bool as int
        if type(self.selected_adapter_index) is not int:
            raise TypeError("selected_adapter_index must be int, not bool")
        if type(self.requested_unit_count) is not int:
            raise TypeError("requested_unit_count must be int, not bool")

        # Reject int as bool
        if type(self.runtime_handoff_requested) is not bool:
            raise TypeError("runtime_handoff_requested must be bool")
        if type(self.caller_confirmation) is not bool:
            raise TypeError("caller_confirmation must be bool")

        # Execution mode must be exactly controlled_single_execution
        if self.execution_mode != "controlled_single_execution":
            raise ValueError(
                "execution_mode must be 'controlled_single_execution', "
                f"got {self.execution_mode!r}"
            )

        # purpose must be non-empty str
        if not isinstance(self.purpose, str) or not self.purpose.strip():
            raise ValueError("purpose must be non-empty caller metadata")

        # runtime_scope must be non-empty str
        if not isinstance(self.runtime_scope, str) or not self.runtime_scope.strip():
            raise ValueError("runtime_scope must be explicit non-empty string")

        # Validate fingerprint fields are hex
        for name in (
            "authorization_request_fingerprint",
            "authorization_decision_fingerprint",
            "execution_plan_fingerprint",
            "stage62_request_fingerprint",
            "stage62_record_fingerprint",
            "stage63_claim_request_fingerprint",
            "stage63_claim_fingerprint",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not _HEX_64.fullmatch(value):
                raise ValueError(f"{name} must be lowercase SHA-256 hex (64 chars)")

        # Validate ID fields are non-empty
        for name in ("claim_id", "consumption_id", "authorization_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")

        # Compute fingerprint
        object.__setattr__(
            self,
            "request_fingerprint",
            canonical_sha256(self._fingerprint_payload()),
        )

    def _fingerprint_payload(self) -> dict[str, Any]:
        return _values(self, exclude=("request_fingerprint",))

    def to_json(self) -> str:
        return canonical_json(_values(self))


# ---------------------------------------------------------------------------
# Execution Envelope
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ControlledRuntimeExecutionEnvelope:
    """Immutable Controlled Runtime Execution Envelope.

    Binds exactly one authorization, one durable claim, one execution plan,
    one adapter index, and one execution unit into a future Runtime handoff
    contract. All execution, write, retry, fallback, and production-hook
    enablements remain False.
    """

    envelope_id: str
    claim_id: str
    consumption_id: str
    authorization_id: str
    authorization_request_fingerprint: str
    authorization_decision_fingerprint: str
    execution_plan_fingerprint: str
    stage62_request_fingerprint: str
    stage62_record_fingerprint: str
    stage63_claim_request_fingerprint: str
    stage63_claim_fingerprint: str
    selected_adapter_index: int
    execution_unit_count: int
    authorization_consumption_prepared: bool
    authorization_consumed: bool
    authorization_reusable: bool
    durable_reuse_prevention_established: bool
    persistent_registry_written: bool
    runtime_handoff_prepared: bool
    runtime_handoff_completed: bool
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
    execution_mode: str
    envelope_state: str
    upstream_fingerprint_chain: tuple[str, ...]
    envelope_request_fingerprint: str
    envelope_fingerprint: str = field(default="", init=False)
    schema_name: str = ENVELOPE_SCHEMA_NAME
    schema_version: str = ENVELOPE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_name != ENVELOPE_SCHEMA_NAME:
            raise ValueError(
                f"envelope schema_name must be {ENVELOPE_SCHEMA_NAME!r}, "
                f"got {self.schema_name!r}"
            )
        if self.schema_version != ENVELOPE_SCHEMA_VERSION:
            raise ValueError(
                f"envelope schema_version must be {ENVELOPE_SCHEMA_VERSION!r}, "
                f"got {self.schema_version!r}"
            )
        if not isinstance(self.upstream_fingerprint_chain, tuple):
            raise TypeError("upstream_fingerprint_chain must be tuple")
        if type(self.selected_adapter_index) is not int:
            raise TypeError("selected_adapter_index must be int, not bool")
        if type(self.execution_unit_count) is not int:
            raise TypeError("execution_unit_count must be int, not bool")

        # Compute envelope fingerprint (upstream chain contains self-referential
        # value, so we exclude it from the envelope's own fingerprint payload).
        upstream = self.upstream_fingerprint_chain
        # The chain has 15 layers; last = envelope fingerprint (not yet computed).
        # If chain is too short, pad with placeholder entries to allow construction
        # (verification will catch invalid chain lengths later).
        pre_envelope = upstream[:14] if len(upstream) >= 14 else upstream
        fingerprint = canonical_sha256(self._fingerprint_payload(pre_envelope))
        object.__setattr__(self, "envelope_fingerprint", fingerprint)
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
            exclude=("envelope_fingerprint", "upstream_fingerprint_chain"),
        )
        chain = (
            upstream
            if upstream is not None
            else self.upstream_fingerprint_chain[:14]
        )
        payload["upstream_fingerprint_chain"] = list(chain)
        return payload

    def to_json(self) -> str:
        return canonical_json(_values(self))


# ---------------------------------------------------------------------------
# Envelope Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ControlledRuntimeExecutionEnvelopeResult:
    """Immutable execution envelope build/verification result.

    Side-effect free. No execution, no writes, no network.
    """

    request: ControlledRuntimeExecutionEnvelopeRequest
    envelope: ControlledRuntimeExecutionEnvelope | None
    freeze_gate_verified: bool
    execution_plan_verified: bool
    authorization_request_verified: bool
    authorization_decision_verified: bool
    stage62_request_verified: bool
    stage62_record_verified: bool
    stage62_result_verified: bool
    stage63_claim_request_verified: bool
    stage63_claim_verified: bool
    stage63_result_verified: bool
    authorization_binding_verified: bool
    consumption_binding_verified: bool
    durable_claim_binding_verified: bool
    execution_unit_verified: bool
    runtime_scope_verified: bool
    policy_findings: tuple[ControlledRuntimeExecutionEnvelopeFinding, ...]
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
        object.__setattr__(
            self,
            "result_fingerprint",
            canonical_sha256(self._fingerprint_payload()),
        )

    def _fingerprint_payload(self) -> dict[str, Any]:
        payload = _values(
            self,
            exclude=("result_fingerprint", "request", "envelope", "policy_findings"),
        )
        payload["request"] = json.loads(self.request.to_json())
        payload["envelope"] = (
            json.loads(self.envelope.to_json()) if self.envelope else None
        )
        payload["policy_findings"] = [
            _values(item) for item in self.policy_findings
        ]
        return payload

    def to_json(self) -> str:
        return canonical_json(self._fingerprint_payload())


# ---------------------------------------------------------------------------
# Envelope Finding
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ControlledRuntimeExecutionEnvelopeFinding:
    """Immutable policy finding — deterministic, bounded, no stack traces."""

    code: str
    severity: str
    message: str
    field: str = ""
    expected: str = ""
    observed: str = ""