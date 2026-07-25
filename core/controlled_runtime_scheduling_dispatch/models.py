"""Immutable deterministic Stage 7.2 scheduling and dispatch models."""

from __future__ import annotations

from dataclasses import dataclass, field

from .policy import (
    ADMISSION_CLASS,
    BOUNDARY_KIND,
    DISPATCH_SCHEMA_NAME,
    DISPATCH_SCHEMA_VERSION,
    FAILURE_STATUS,
    PRIORITY_CLASS,
    REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION,
    RESULT_SCHEMA_NAME,
    RESULT_SCHEMA_VERSION,
    SCHEDULE_SCHEMA_NAME,
    SCHEDULE_SCHEMA_VERSION,
    SCHEDULE_STATE,
    SCHEDULING_INTENT,
    SUCCESS_STATUS,
    VERIFICATION_SCHEMA_NAME,
    VERIFICATION_SCHEMA_VERSION,
)
from .serialization import canonical_sha256, values

_HEX = frozenset("0123456789abcdef")


def _text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")


def _fingerprint(name: str, value: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise ValueError(f"{name} must be lowercase SHA-256 hex")


def _identity(prefix: str, payload: object) -> str:
    return f"{prefix}-{canonical_sha256(payload)[:32]}"


def _validate_binding_fields(instance) -> None:
    for name in (
        "queue_record_id",
        "admission_request_id",
        "stage613_claim_id",
        "stage612_record_id",
        "stage611_claim_id",
        "stage610_authorization_id",
        "stage69_consumption_claim_id",
        "stage68_scheduling_envelope_id",
        "stage67_consumption_claim_id",
        "stage66_scheduling_authorization_id",
        "runtime_boundary_id",
        "ordering_key",
    ):
        _text(name, getattr(instance, name))
    for name in (
        "queue_record_fingerprint",
        "admission_request_fingerprint",
        "stage613_claim_fingerprint",
        "stage612_record_fingerprint",
        "stage611_claim_fingerprint",
        "stage610_decision_fingerprint",
        "stage69_claim_fingerprint",
        "stage68_envelope_fingerprint",
        "stage67_claim_fingerprint",
        "stage66_decision_fingerprint",
        "capability_state_fingerprint",
        "execution_plan_reference_fingerprint",
        "work_package_reference_fingerprint",
    ):
        _fingerprint(name, getattr(instance, name))
    if instance.runtime_boundary_kind != BOUNDARY_KIND:
        raise ValueError("invalid runtime-boundary kind")
    if type(instance.selected_adapter_index) is not int:
        raise TypeError("selected_adapter_index must be int, not bool")
    if instance.selected_adapter_index < 0:
        raise ValueError("selected_adapter_index must be non-negative")
    if type(instance.unit_scope) is not int:
        raise TypeError("unit_scope must be int, not bool")
    if instance.unit_scope != 1:
        raise ValueError("unit_scope must be exactly 1")
    if instance.admission_class != ADMISSION_CLASS:
        raise ValueError("invalid admission class")
    if instance.priority_class != PRIORITY_CLASS:
        raise ValueError("invalid priority class")


@dataclass(frozen=True)
class ControlledRuntimeSchedulingRequest:
    queue_record_id: str
    queue_record_fingerprint: str
    admission_request_id: str
    admission_request_fingerprint: str
    stage613_claim_id: str
    stage613_claim_fingerprint: str
    stage612_record_id: str
    stage612_record_fingerprint: str
    stage611_claim_id: str
    stage611_claim_fingerprint: str
    stage610_authorization_id: str
    stage610_decision_fingerprint: str
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
    execution_plan_reference_fingerprint: str
    work_package_reference_fingerprint: str
    upstream_chain: tuple[str, ...]
    scheduling_intent: str = SCHEDULING_INTENT
    schema_name: str = REQUEST_SCHEMA_NAME
    schema_version: str = REQUEST_SCHEMA_VERSION
    scheduling_request_id: str = field(default="", init=False)
    request_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            REQUEST_SCHEMA_NAME,
            REQUEST_SCHEMA_VERSION,
        ):
            raise ValueError("invalid Stage 7.2 scheduling-request schema")
        _validate_binding_fields(self)
        if self.scheduling_intent != SCHEDULING_INTENT:
            raise ValueError("invalid scheduling intent")
        if not isinstance(self.upstream_chain, tuple) or len(self.upstream_chain) != 35:
            raise ValueError("upstream_chain must contain exactly 35 layers")
        for index, item in enumerate(self.upstream_chain):
            _fingerprint(f"upstream_chain[{index}]", item)
        if len(set(self.upstream_chain)) != 35:
            raise ValueError("upstream chain layers must be unique")
        if self.upstream_chain[-1] != self.queue_record_fingerprint:
            raise ValueError("Stage 7.1 terminal fingerprint mismatch")
        if self.upstream_chain[6] != self.execution_plan_reference_fingerprint:
            raise ValueError("execution-plan reference mismatch")
        if self.upstream_chain[0] != self.work_package_reference_fingerprint:
            raise ValueError("work-package reference mismatch")
        identity = _identity(
            "stage72-scheduling-request",
            values(self, exclude=("scheduling_request_id", "request_fingerprint")),
        )
        object.__setattr__(self, "scheduling_request_id", identity)
        object.__setattr__(
            self,
            "request_fingerprint",
            canonical_sha256(values(self, exclude=("request_fingerprint",))),
        )

    def to_json(self) -> str:
        from .serialization import canonical_json

        return canonical_json(values(self))


@dataclass(frozen=True)
class ControlledRuntimeExecutionSchedule:
    scheduling_request_id: str
    scheduling_request_fingerprint: str
    queue_record_id: str
    queue_record_fingerprint: str
    admission_request_id: str
    admission_request_fingerprint: str
    stage613_claim_id: str
    stage613_claim_fingerprint: str
    stage612_record_id: str
    stage612_record_fingerprint: str
    stage611_claim_id: str
    stage611_claim_fingerprint: str
    stage610_authorization_id: str
    stage610_decision_fingerprint: str
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
    execution_plan_reference_fingerprint: str
    work_package_reference_fingerprint: str
    dispatch_key: str
    schedule_state: str
    queue_record_created: bool
    queue_record_consumed: bool
    queue_record_reusable: bool
    runtime_execution_scheduled: bool
    dispatch_package_created: bool
    execution_started: bool
    runtime_executor_invoked: bool
    worker_started: bool
    provider_execution_started: bool
    translation_execution_started: bool
    output_written: bool
    canonical_chain: tuple[str, ...]
    schema_name: str = SCHEDULE_SCHEMA_NAME
    schema_version: str = SCHEDULE_SCHEMA_VERSION
    schedule_id: str = field(default="", init=False)
    schedule_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            SCHEDULE_SCHEMA_NAME,
            SCHEDULE_SCHEMA_VERSION,
        ):
            raise ValueError("invalid Stage 7.2 execution-schedule schema")
        _text("scheduling_request_id", self.scheduling_request_id)
        _fingerprint(
            "scheduling_request_fingerprint",
            self.scheduling_request_fingerprint,
        )
        _validate_binding_fields(self)
        _text("dispatch_key", self.dispatch_key)
        if self.schedule_state != SCHEDULE_STATE:
            raise ValueError("invalid immutable schedule state")
        expected = {
            "queue_record_created": True,
            "queue_record_consumed": True,
            "queue_record_reusable": False,
            "runtime_execution_scheduled": True,
            "dispatch_package_created": True,
            "execution_started": False,
            "runtime_executor_invoked": False,
            "worker_started": False,
            "provider_execution_started": False,
            "translation_execution_started": False,
            "output_written": False,
        }
        for name, required in expected.items():
            if type(getattr(self, name)) is not bool or getattr(self, name) is not required:
                raise ValueError(f"{name} invariant violated")
        if not isinstance(self.canonical_chain, tuple) or len(self.canonical_chain) not in (36, 37):
            raise ValueError("schedule chain must have 36 or 37 layers")
        pre_chain = self.canonical_chain[:36]
        if len(set(pre_chain)) != 36:
            raise ValueError("schedule chain layers must be unique")
        if pre_chain[-1] != self.scheduling_request_fingerprint:
            raise ValueError("scheduling-request layer must precede schedule")
        identity = _identity(
            "stage72-runtime-execution-schedule",
            self._payload(pre_chain, schedule_id=""),
        )
        object.__setattr__(self, "schedule_id", identity)
        fingerprint = canonical_sha256(self._payload(pre_chain, schedule_id=identity))
        object.__setattr__(self, "schedule_fingerprint", fingerprint)
        object.__setattr__(self, "canonical_chain", pre_chain + (fingerprint,))

    def _payload(self, chain: tuple[str, ...], *, schedule_id: str):
        payload = values(
            self,
            exclude=("schedule_id", "schedule_fingerprint", "canonical_chain"),
        )
        payload["schedule_id"] = schedule_id
        payload["canonical_chain"] = list(chain)
        return payload

    def to_json(self) -> str:
        from .serialization import canonical_json

        return canonical_json(values(self))


@dataclass(frozen=True)
class ControlledRuntimeDispatchPackage:
    schedule_id: str
    schedule_fingerprint: str
    scheduling_request_id: str
    scheduling_request_fingerprint: str
    queue_record_id: str
    queue_record_fingerprint: str
    admission_request_id: str
    admission_request_fingerprint: str
    stage613_claim_id: str
    stage613_claim_fingerprint: str
    stage612_record_id: str
    stage612_record_fingerprint: str
    stage611_claim_id: str
    stage611_claim_fingerprint: str
    stage610_authorization_id: str
    stage610_decision_fingerprint: str
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
    execution_plan_reference_fingerprint: str
    work_package_reference_fingerprint: str
    dispatch_key: str
    dispatch_package_created: bool
    execution_started: bool
    runtime_executor_invoked: bool
    worker_started: bool
    provider_execution_started: bool
    translation_execution_started: bool
    output_written: bool
    canonical_chain: tuple[str, ...]
    schema_name: str = DISPATCH_SCHEMA_NAME
    schema_version: str = DISPATCH_SCHEMA_VERSION
    dispatch_package_id: str = field(default="", init=False)
    dispatch_fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            DISPATCH_SCHEMA_NAME,
            DISPATCH_SCHEMA_VERSION,
        ):
            raise ValueError("invalid Stage 7.2 dispatch-package schema")
        _text("schedule_id", self.schedule_id)
        _fingerprint("schedule_fingerprint", self.schedule_fingerprint)
        _text("scheduling_request_id", self.scheduling_request_id)
        _fingerprint(
            "scheduling_request_fingerprint",
            self.scheduling_request_fingerprint,
        )
        _validate_binding_fields(self)
        _text("dispatch_key", self.dispatch_key)
        expected = {
            "dispatch_package_created": True,
            "execution_started": False,
            "runtime_executor_invoked": False,
            "worker_started": False,
            "provider_execution_started": False,
            "translation_execution_started": False,
            "output_written": False,
        }
        for name, required in expected.items():
            if type(getattr(self, name)) is not bool or getattr(self, name) is not required:
                raise ValueError(f"{name} invariant violated")
        if not isinstance(self.canonical_chain, tuple) or len(self.canonical_chain) not in (37, 38):
            raise ValueError("dispatch chain must have 37 or 38 layers")
        pre_chain = self.canonical_chain[:37]
        if len(set(pre_chain)) != 37:
            raise ValueError("dispatch chain layers must be unique")
        if pre_chain[-1] != self.schedule_fingerprint:
            raise ValueError("schedule layer must precede dispatch")
        identity = _identity(
            "stage72-runtime-dispatch-package",
            self._payload(pre_chain, dispatch_package_id=""),
        )
        object.__setattr__(self, "dispatch_package_id", identity)
        fingerprint = canonical_sha256(
            self._payload(pre_chain, dispatch_package_id=identity)
        )
        object.__setattr__(self, "dispatch_fingerprint", fingerprint)
        object.__setattr__(self, "canonical_chain", pre_chain + (fingerprint,))

    def _payload(self, chain: tuple[str, ...], *, dispatch_package_id: str):
        payload = values(
            self,
            exclude=(
                "dispatch_package_id",
                "dispatch_fingerprint",
                "canonical_chain",
            ),
        )
        payload["dispatch_package_id"] = dispatch_package_id
        payload["canonical_chain"] = list(chain)
        return payload

    def to_json(self) -> str:
        from .serialization import canonical_json

        return canonical_json(values(self))


@dataclass(frozen=True)
class ControlledRuntimeSchedulingDispatchVerificationResult:
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
    schedule_readback_verified: bool
    dispatch_readback_verified: bool
    canonical_payload_verified: bool
    zero_side_effects_verified: bool
    reason_codes: tuple[str, ...]
    schema_name: str = VERIFICATION_SCHEMA_NAME
    schema_version: str = VERIFICATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (self.schema_name, self.schema_version) != (
            VERIFICATION_SCHEMA_NAME,
            VERIFICATION_SCHEMA_VERSION,
        ):
            raise ValueError("invalid Stage 7.2 verification-result schema")
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
            "schedule_readback_verified",
            "dispatch_readback_verified",
            "canonical_payload_verified",
            "zero_side_effects_verified",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")
        if not isinstance(self.reason_codes, tuple):
            raise TypeError("reason_codes must be an immutable tuple")


@dataclass(frozen=True)
class ControlledRuntimeSchedulingResult:
    request: ControlledRuntimeSchedulingRequest
    schedule: ControlledRuntimeExecutionSchedule | None
    dispatch_package: ControlledRuntimeDispatchPackage | None
    verification_succeeded: bool
    upstream_verified: bool
    queue_record_consumed: bool
    runtime_execution_scheduled: bool
    dispatch_package_created: bool
    replay_detected: bool
    conflict_detected: bool
    persistence_committed: bool
    schedule_readback_verified: bool
    dispatch_readback_verified: bool
    status: str
    reason_codes: tuple[str, ...]
    queue_record_consumed_count: int
    runtime_schedule_count: int
    dispatch_package_count: int
    runtime_execution_count: int = 0
    worker_started_count: int = 0
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
            raise ValueError("invalid Stage 7.2 scheduling-result schema")
        if self.status not in (SUCCESS_STATUS, FAILURE_STATUS):
            raise ValueError("invalid Stage 7.2 result status")
        if not isinstance(self.request, ControlledRuntimeSchedulingRequest):
            raise TypeError("request must be a Stage 7.2 scheduling request")
        for name in (
            "verification_succeeded",
            "upstream_verified",
            "queue_record_consumed",
            "runtime_execution_scheduled",
            "dispatch_package_created",
            "replay_detected",
            "conflict_detected",
            "persistence_committed",
            "schedule_readback_verified",
            "dispatch_readback_verified",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")
        if not isinstance(self.reason_codes, tuple):
            raise TypeError("reason_codes must be tuple")
        count_names = (
            "queue_record_consumed_count",
            "runtime_schedule_count",
            "dispatch_package_count",
            "runtime_execution_count",
            "worker_started_count",
            "provider_execution_count",
            "network_execution_count",
            "translation_execution_count",
            "output_write_count",
            "resume_write_count",
            "cache_write_count",
        )
        if any(type(getattr(self, name)) is not int or getattr(self, name) < 0 for name in count_names):
            raise ValueError("result counts must be non-negative integers")
        if self.status == SUCCESS_STATUS and not all(
            (
                isinstance(self.schedule, ControlledRuntimeExecutionSchedule),
                isinstance(self.dispatch_package, ControlledRuntimeDispatchPackage),
                self.verification_succeeded,
                self.upstream_verified,
                self.queue_record_consumed,
                self.runtime_execution_scheduled,
                self.dispatch_package_created,
                not self.replay_detected,
                not self.conflict_detected,
                self.persistence_committed,
                self.schedule_readback_verified,
                self.dispatch_readback_verified,
                self.queue_record_consumed_count == 1,
                self.runtime_schedule_count == 1,
                self.dispatch_package_count == 1,
                not self.reason_codes,
                all(getattr(self, name) == 0 for name in count_names[3:]),
            )
        ):
            raise ValueError("success-result invariant violated")
