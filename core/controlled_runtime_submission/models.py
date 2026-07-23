from __future__ import annotations

import json
import re
from dataclasses import dataclass


RuntimeSubmissionFindingValue = str | int | float | bool | None
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class RuntimeSubmissionSourceReference:
    source_name: str
    source_content_fingerprint: str
    execution_package_fingerprint: str
    authorization_fingerprint: str
    approval_record_fingerprint: str
    manifest_fingerprint: str
    segmentation_fingerprint: str
    chunk_plan_fingerprint: str
    preparation_fingerprint: str

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if name.endswith("_fingerprint") and not _HEX_64.fullmatch(value):
                raise ValueError(f"{name} must be lowercase SHA-256 hex")


@dataclass(frozen=True)
class RuntimeSubmissionUnit:
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
        ):
            if not _HEX_64.fullmatch(getattr(self, name)):
                raise ValueError(f"{name} must be lowercase SHA-256 hex")
        if self.character_count != len(self.text):
            raise ValueError("character_count must equal len(text)")
        if self.source_character_end - self.source_character_start != len(self.text):
            raise ValueError("unit offsets must match text length")


@dataclass(frozen=True)
class RuntimeSubmissionFinding:
    code: str
    severity: str
    message: str
    unit_index: int | None = None
    observed_value: RuntimeSubmissionFindingValue = None
    required_value: RuntimeSubmissionFindingValue = None


@dataclass(frozen=True)
class RuntimeSubmissionPackage:
    schema_name: str
    schema_version: str
    strategy: str
    activation_gate: str
    source: RuntimeSubmissionSourceReference
    units: tuple[RuntimeSubmissionUnit, ...]
    approved_unit_indices: tuple[int, ...]
    submission_unit_count: int
    original_execution_unit_count: int
    character_count: int
    covered_character_count: int
    coverage_ratio: float
    approved_character_count: int
    original_character_count: int
    approval_coverage_ratio: float
    status: str
    action: str
    findings: tuple[RuntimeSubmissionFinding, ...]
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
    runtime_submission_package_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.units, tuple):
            raise TypeError("units must be a tuple")
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be a tuple")
        if not isinstance(self.approved_unit_indices, tuple):
            raise TypeError("approved_unit_indices must be a tuple")
        if self.submission_unit_count != len(self.units):
            raise ValueError("submission_unit_count must equal len(units)")
        if self.approved_unit_indices != tuple(
            unit.execution_unit_index for unit in self.units
        ):
            raise ValueError("approved_unit_indices must match submission units")
        if not _HEX_64.fullmatch(self.runtime_submission_package_fingerprint):
            raise ValueError(
                "runtime_submission_package_fingerprint must be lowercase SHA-256 hex"
            )

    @property
    def is_full_package_submission(self) -> bool:
        return (
            self.original_execution_unit_count > 0
            and self.approved_unit_indices
            == tuple(range(self.original_execution_unit_count))
        )

    def reconstruct_approved_text(self) -> str:
        return "".join(unit.text for unit in self.units)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "strategy": self.strategy,
            "activation_gate": self.activation_gate,
            "source": {
                "source_name": self.source.source_name,
                "source_content_fingerprint": self.source.source_content_fingerprint,
                "execution_package_fingerprint": self.source.execution_package_fingerprint,
                "authorization_fingerprint": self.source.authorization_fingerprint,
                "approval_record_fingerprint": self.source.approval_record_fingerprint,
                "manifest_fingerprint": self.source.manifest_fingerprint,
                "segmentation_fingerprint": self.source.segmentation_fingerprint,
                "chunk_plan_fingerprint": self.source.chunk_plan_fingerprint,
                "preparation_fingerprint": self.source.preparation_fingerprint,
            },
            "units": [
                {
                    "submission_index": unit.submission_index,
                    "execution_unit_index": unit.execution_unit_index,
                    "execution_unit_id": unit.execution_unit_id,
                    "text": unit.text,
                    "source_character_start": unit.source_character_start,
                    "source_character_end": unit.source_character_end,
                    "section_indices": list(unit.section_indices),
                    "heading_text": unit.heading_text,
                    "boundary_reason": unit.boundary_reason,
                    "character_count": unit.character_count,
                    "non_whitespace_character_count": unit.non_whitespace_character_count,
                    "source_chunk_fingerprint": unit.source_chunk_fingerprint,
                    "execution_unit_fingerprint": unit.execution_unit_fingerprint,
                    "runtime_submission_unit_fingerprint": unit.runtime_submission_unit_fingerprint,
                    "status": unit.status,
                    "runtime_attempt_count": unit.runtime_attempt_count,
                    "provider_request_count": unit.provider_request_count,
                    "translation_result_attached": unit.translation_result_attached,
                }
                for unit in self.units
            ],
            "approved_unit_indices": list(self.approved_unit_indices),
            "submission_unit_count": self.submission_unit_count,
            "original_execution_unit_count": self.original_execution_unit_count,
            "character_count": self.character_count,
            "covered_character_count": self.covered_character_count,
            "coverage_ratio": self.coverage_ratio,
            "approved_character_count": self.approved_character_count,
            "original_character_count": self.original_character_count,
            "approval_coverage_ratio": self.approval_coverage_ratio,
            "status": self.status,
            "action": self.action,
            "findings": [
                {
                    "code": finding.code,
                    "severity": finding.severity,
                    "message": finding.message,
                    "unit_index": finding.unit_index,
                    "observed_value": finding.observed_value,
                    "required_value": finding.required_value,
                }
                for finding in self.findings
            ],
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
            "runtime_submission_package_fingerprint": self.runtime_submission_package_fingerprint,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
