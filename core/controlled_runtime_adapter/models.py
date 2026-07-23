from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass


RuntimeAdapterFindingValue = str | int | float | bool | None
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class RuntimeAdapterSourceReference:
    source_name: str
    source_content_fingerprint: str
    execution_package_fingerprint: str
    authorization_fingerprint: str
    approval_record_fingerprint: str
    runtime_submission_package_fingerprint: str
    manifest_fingerprint: str
    segmentation_fingerprint: str
    chunk_plan_fingerprint: str
    preparation_fingerprint: str

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if name.endswith("_fingerprint") and not _HEX_64.fullmatch(value):
                raise ValueError(f"{name} must be lowercase SHA-256 hex")


@dataclass(frozen=True)
class RuntimeAdapterCapabilityProfile:
    profile_name: str
    profile_version: str
    supports_controlled_submission: bool
    supports_partial_scope: bool
    supports_full_package_scope: bool
    supports_provider_execution: bool
    supports_translation_execution: bool
    supports_automatic_retry: bool
    supports_automatic_fallback: bool
    supports_output_replacement: bool
    supports_resume_write: bool
    supports_cache_write: bool
    supports_output_write: bool
    supports_production_hook: bool


@dataclass(frozen=True)
class RuntimeAdapterUnit:
    adapter_unit_index: int
    submission_index: int
    execution_unit_index: int
    execution_unit_id: str
    text: str
    source_character_start: int
    source_character_end: int
    section_indices: tuple[int, ...]
    heading_text: str | None
    boundary_reason: str
    character_count: int
    non_whitespace_character_count: int
    source_chunk_fingerprint: str
    execution_unit_fingerprint: str
    runtime_submission_unit_fingerprint: str
    runtime_adapter_unit_fingerprint: str
    status: str
    runtime_attempt_count: int
    provider_request_count: int
    translation_result_attached: bool

    def __post_init__(self) -> None:
        if not isinstance(self.section_indices, tuple):
            raise TypeError("section_indices must be a tuple")
        for name in (
            "source_chunk_fingerprint",
            "execution_unit_fingerprint",
            "runtime_submission_unit_fingerprint",
            "runtime_adapter_unit_fingerprint",
        ):
            if not _HEX_64.fullmatch(getattr(self, name)):
                raise ValueError(f"{name} must be lowercase SHA-256 hex")
        if self.character_count != len(self.text):
            raise ValueError("character_count must equal len(text)")
        if self.source_character_end - self.source_character_start != len(self.text):
            raise ValueError("unit offsets must match text length")


@dataclass(frozen=True)
class RuntimeAdapterFinding:
    code: str
    severity: str
    message: str
    unit_index: int | None = None
    observed_value: RuntimeAdapterFindingValue = None
    required_value: RuntimeAdapterFindingValue = None


@dataclass(frozen=True)
class RuntimeAdapterRequest:
    schema_name: str
    schema_version: str
    strategy: str
    activation_gate: str
    source: RuntimeAdapterSourceReference
    capability_profile: RuntimeAdapterCapabilityProfile
    units: tuple[RuntimeAdapterUnit, ...]
    approved_unit_indices: tuple[int, ...]
    adapter_unit_count: int
    original_execution_unit_count: int
    approved_character_count: int
    original_character_count: int
    approval_coverage_ratio: float
    status: str
    action: str
    findings: tuple[RuntimeAdapterFinding, ...]
    summary: str
    provider_execution_authorized: bool
    translation_execution_authorized: bool
    runtime_submission_authorized: bool
    automatic_retry_authorized: bool
    automatic_fallback_authorized: bool
    output_replacement_authorized: bool
    runtime_submission_executed: bool
    provider_requests_executed: int
    translation_executions_completed: int
    runtime_adapter_request_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.units, tuple):
            raise TypeError("units must be a tuple")
        if not isinstance(self.approved_unit_indices, tuple):
            raise TypeError("approved_unit_indices must be a tuple")
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be a tuple")
        if self.adapter_unit_count != len(self.units):
            raise ValueError("adapter_unit_count must equal len(units)")
        if self.approved_unit_indices != tuple(
            unit.execution_unit_index for unit in self.units
        ):
            raise ValueError("approved_unit_indices must match adapter units")
        if not _HEX_64.fullmatch(self.runtime_adapter_request_fingerprint):
            raise ValueError(
                "runtime_adapter_request_fingerprint must be lowercase SHA-256 hex"
            )

    @property
    def is_full_package_request(self) -> bool:
        return (
            self.original_execution_unit_count > 0
            and self.approved_unit_indices
            == tuple(range(self.original_execution_unit_count))
        )

    @property
    def is_partial_scope_request(self) -> bool:
        return not self.is_full_package_request

    def reconstruct_approved_text(self) -> str:
        return "".join(unit.text for unit in self.units)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "strategy": self.strategy,
            "activation_gate": self.activation_gate,
            "source": asdict(self.source),
            "capability_profile": asdict(self.capability_profile),
            "units": [
                {
                    **asdict(unit),
                    "section_indices": list(unit.section_indices),
                }
                for unit in self.units
            ],
            "approved_unit_indices": list(self.approved_unit_indices),
            "adapter_unit_count": self.adapter_unit_count,
            "original_execution_unit_count": self.original_execution_unit_count,
            "approved_character_count": self.approved_character_count,
            "original_character_count": self.original_character_count,
            "approval_coverage_ratio": self.approval_coverage_ratio,
            "status": self.status,
            "action": self.action,
            "findings": [asdict(finding) for finding in self.findings],
            "summary": self.summary,
            "provider_execution_authorized": self.provider_execution_authorized,
            "translation_execution_authorized": self.translation_execution_authorized,
            "runtime_submission_authorized": self.runtime_submission_authorized,
            "automatic_retry_authorized": self.automatic_retry_authorized,
            "automatic_fallback_authorized": self.automatic_fallback_authorized,
            "output_replacement_authorized": self.output_replacement_authorized,
            "runtime_submission_executed": self.runtime_submission_executed,
            "provider_requests_executed": self.provider_requests_executed,
            "translation_executions_completed": self.translation_executions_completed,
            "runtime_adapter_request_fingerprint": self.runtime_adapter_request_fingerprint,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )


@dataclass(frozen=True)
class RuntimeAdapterPreparationResult:
    request: RuntimeAdapterRequest
    capability_profile: RuntimeAdapterCapabilityProfile
    prepared: bool
    compatible: bool
    runtime_invoked: bool
    provider_invoked: bool
    translation_invoked: bool
    status: str
    action: str
    findings: tuple[RuntimeAdapterFinding, ...]
    summary: str
    preparation_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be a tuple")
        if not _HEX_64.fullmatch(self.preparation_fingerprint):
            raise ValueError("preparation_fingerprint must be lowercase SHA-256 hex")

    def to_dict(self) -> dict[str, object]:
        return {
            "request": self.request.to_dict(),
            "capability_profile": asdict(self.capability_profile),
            "prepared": self.prepared,
            "compatible": self.compatible,
            "runtime_invoked": self.runtime_invoked,
            "provider_invoked": self.provider_invoked,
            "translation_invoked": self.translation_invoked,
            "status": self.status,
            "action": self.action,
            "findings": [asdict(finding) for finding in self.findings],
            "summary": self.summary,
            "preparation_fingerprint": self.preparation_fingerprint,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
