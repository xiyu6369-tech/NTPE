from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass


ControlledRuntimeExecutionFindingValue = str | int | float | bool | None
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ControlledRuntimeExecutionSourceReference:
    source_name: str
    source_content_fingerprint: str
    execution_package_fingerprint: str
    authorization_fingerprint: str
    approval_record_fingerprint: str
    runtime_submission_package_fingerprint: str
    runtime_adapter_request_fingerprint: str
    runtime_adapter_preparation_fingerprint: str
    manifest_fingerprint: str
    segmentation_fingerprint: str
    chunk_plan_fingerprint: str
    preparation_fingerprint: str

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if name.endswith("_fingerprint") and not _HEX_64.fullmatch(value):
                raise ValueError(f"{name} must be lowercase SHA-256 hex")


@dataclass(frozen=True)
class ControlledRuntimeExecutionPolicy:
    policy_name: str
    policy_version: str
    execution_mode: str
    maximum_units_per_execution: int
    maximum_provider_requests_per_unit: int
    maximum_total_provider_requests: int
    allow_partial_scope: bool
    allow_full_package_scope: bool
    allow_parallel_execution: bool
    allow_automatic_retry: bool
    allow_automatic_fallback: bool
    allow_output_replacement: bool
    allow_output_write: bool
    allow_resume_write: bool
    allow_cache_write: bool
    allow_production_hook: bool
    runtime_execution_enabled: bool
    provider_execution_enabled: bool
    translation_execution_enabled: bool


@dataclass(frozen=True)
class ControlledRuntimeExecutionStep:
    step_index: int
    adapter_unit_index: int
    submission_index: int
    execution_unit_index: int
    execution_unit_id: str
    text: str
    source_character_start: int
    source_character_end: int
    section_indices: tuple[int, ...]
    source_chunk_fingerprint: str
    execution_unit_fingerprint: str
    runtime_submission_unit_fingerprint: str
    runtime_adapter_unit_fingerprint: str
    planned_provider_request_limit: int
    planned_retry_limit: int
    planned_fallback_limit: int
    status: str
    runtime_attempt_count: int
    provider_request_count: int
    translation_result_attached: bool
    execution_step_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.section_indices, tuple):
            raise TypeError("section_indices must be a tuple")
        for name in (
            "source_chunk_fingerprint",
            "execution_unit_fingerprint",
            "runtime_submission_unit_fingerprint",
            "runtime_adapter_unit_fingerprint",
            "execution_step_fingerprint",
        ):
            if not _HEX_64.fullmatch(getattr(self, name)):
                raise ValueError(f"{name} must be lowercase SHA-256 hex")
        if self.source_character_end - self.source_character_start != len(self.text):
            raise ValueError("step offsets must match text length")


@dataclass(frozen=True)
class ControlledRuntimeExecutionFinding:
    code: str
    severity: str
    message: str
    step_index: int | None = None
    observed_value: ControlledRuntimeExecutionFindingValue = None
    required_value: ControlledRuntimeExecutionFindingValue = None


@dataclass(frozen=True)
class ControlledRuntimeExecutionPlan:
    schema_name: str
    schema_version: str
    strategy: str
    activation_gate: str
    source: ControlledRuntimeExecutionSourceReference
    policy: ControlledRuntimeExecutionPolicy
    steps: tuple[ControlledRuntimeExecutionStep, ...]
    selected_adapter_unit_indices: tuple[int, ...]
    planned_step_count: int
    available_adapter_unit_count: int
    planned_character_count: int
    approved_character_count: int
    planned_approval_coverage_ratio: float
    status: str
    action: str
    findings: tuple[ControlledRuntimeExecutionFinding, ...]
    summary: str
    runtime_execution_authorized: bool
    provider_execution_authorized: bool
    translation_execution_authorized: bool
    runtime_execution_enabled: bool
    provider_execution_enabled: bool
    translation_execution_enabled: bool
    automatic_retry_authorized: bool
    automatic_fallback_authorized: bool
    output_replacement_authorized: bool
    execution_started: bool
    execution_completed: bool
    provider_requests_executed: int
    translation_executions_completed: int
    execution_plan_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.steps, tuple):
            raise TypeError("steps must be a tuple")
        if not isinstance(self.selected_adapter_unit_indices, tuple):
            raise TypeError("selected_adapter_unit_indices must be a tuple")
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be a tuple")
        if self.planned_step_count != len(self.steps):
            raise ValueError("planned_step_count must equal len(steps)")
        if self.selected_adapter_unit_indices != tuple(
            step.adapter_unit_index for step in self.steps
        ):
            raise ValueError("selected indices must match planned steps")
        if not _HEX_64.fullmatch(self.execution_plan_fingerprint):
            raise ValueError("execution_plan_fingerprint must be lowercase SHA-256 hex")

    @property
    def is_single_unit_plan(self) -> bool:
        return len(self.steps) == 1

    @property
    def covers_full_approved_scope(self) -> bool:
        return (
            self.available_adapter_unit_count == 1
            and self.selected_adapter_unit_indices == (0,)
        )

    def reconstruct_planned_text(self) -> str:
        return "".join(step.text for step in self.steps)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "strategy": self.strategy,
            "activation_gate": self.activation_gate,
            "source": asdict(self.source),
            "policy": asdict(self.policy),
            "steps": [
                {**asdict(step), "section_indices": list(step.section_indices)}
                for step in self.steps
            ],
            "selected_adapter_unit_indices": list(
                self.selected_adapter_unit_indices
            ),
            "planned_step_count": self.planned_step_count,
            "available_adapter_unit_count": self.available_adapter_unit_count,
            "planned_character_count": self.planned_character_count,
            "approved_character_count": self.approved_character_count,
            "planned_approval_coverage_ratio": self.planned_approval_coverage_ratio,
            "status": self.status,
            "action": self.action,
            "findings": [asdict(finding) for finding in self.findings],
            "summary": self.summary,
            "runtime_execution_authorized": self.runtime_execution_authorized,
            "provider_execution_authorized": self.provider_execution_authorized,
            "translation_execution_authorized": (
                self.translation_execution_authorized
            ),
            "runtime_execution_enabled": self.runtime_execution_enabled,
            "provider_execution_enabled": self.provider_execution_enabled,
            "translation_execution_enabled": self.translation_execution_enabled,
            "automatic_retry_authorized": self.automatic_retry_authorized,
            "automatic_fallback_authorized": self.automatic_fallback_authorized,
            "output_replacement_authorized": self.output_replacement_authorized,
            "execution_started": self.execution_started,
            "execution_completed": self.execution_completed,
            "provider_requests_executed": self.provider_requests_executed,
            "translation_executions_completed": (
                self.translation_executions_completed
            ),
            "execution_plan_fingerprint": self.execution_plan_fingerprint,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
