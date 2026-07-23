from __future__ import annotations

import json
import re
from dataclasses import dataclass


ExecutionFindingValue = str | int | float | bool | None
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ExecutionSourceReference:
    source_name: str
    source_content_fingerprint: str
    manifest_fingerprint: str
    segmentation_fingerprint: str
    chunk_plan_fingerprint: str
    preparation_fingerprint: str

    def __post_init__(self) -> None:
        for name, value in (
            ("source_content_fingerprint", self.source_content_fingerprint),
            ("manifest_fingerprint", self.manifest_fingerprint),
            ("segmentation_fingerprint", self.segmentation_fingerprint),
            ("chunk_plan_fingerprint", self.chunk_plan_fingerprint),
            ("preparation_fingerprint", self.preparation_fingerprint),
        ):
            if not _HEX_64.fullmatch(value):
                raise ValueError(f"{name} must be lowercase SHA-256 hex")


@dataclass(frozen=True)
class TranslationExecutionUnit:
    index: int
    unit_id: str
    chunk_index: int
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
    status: str
    attempt_count: int
    provider_request_count: int
    translation_result_attached: bool

    def __post_init__(self) -> None:
        if not isinstance(self.section_indices, tuple):
            raise TypeError("section_indices must be a tuple")
        if not _HEX_64.fullmatch(self.source_chunk_fingerprint):
            raise ValueError("source_chunk_fingerprint must be lowercase SHA-256 hex")
        if not _HEX_64.fullmatch(self.execution_unit_fingerprint):
            raise ValueError("execution_unit_fingerprint must be lowercase SHA-256 hex")
        if self.character_count != len(self.text):
            raise ValueError("character_count must equal len(text)")
        if self.source_character_end - self.source_character_start != len(self.text):
            raise ValueError("unit offsets must match text length")


@dataclass(frozen=True)
class ExecutionPackageFinding:
    code: str
    severity: str
    message: str
    unit_index: int | None = None
    observed_value: ExecutionFindingValue = None


@dataclass(frozen=True)
class TranslationExecutionPackage:
    schema_name: str
    schema_version: str
    strategy: str
    activation_gate: str
    source: ExecutionSourceReference
    units: tuple[TranslationExecutionUnit, ...]
    unit_count: int
    character_count: int
    covered_character_count: int
    coverage_ratio: float
    status: str
    action: str
    findings: tuple[ExecutionPackageFinding, ...]
    summary: str
    provider_execution_authorized: bool
    translation_execution_authorized: bool
    runtime_submission_authorized: bool
    automatic_retry_authorized: bool
    automatic_fallback_authorized: bool
    output_replacement_authorized: bool
    execution_package_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.units, tuple) or not isinstance(self.findings, tuple):
            raise TypeError("units and findings must be tuples")
        if self.unit_count != len(self.units):
            raise ValueError("unit_count must equal len(units)")
        if not _HEX_64.fullmatch(self.execution_package_fingerprint):
            raise ValueError("execution_package_fingerprint must be lowercase SHA-256 hex")

    def reconstruct_source_text(self) -> str:
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
                "manifest_fingerprint": self.source.manifest_fingerprint,
                "segmentation_fingerprint": self.source.segmentation_fingerprint,
                "chunk_plan_fingerprint": self.source.chunk_plan_fingerprint,
                "preparation_fingerprint": self.source.preparation_fingerprint,
            },
            "units": [
                {
                    "index": unit.index,
                    "unit_id": unit.unit_id,
                    "chunk_index": unit.chunk_index,
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
                    "status": unit.status,
                    "attempt_count": unit.attempt_count,
                    "provider_request_count": unit.provider_request_count,
                    "translation_result_attached": unit.translation_result_attached,
                }
                for unit in self.units
            ],
            "unit_count": self.unit_count,
            "character_count": self.character_count,
            "covered_character_count": self.covered_character_count,
            "coverage_ratio": self.coverage_ratio,
            "status": self.status,
            "action": self.action,
            "findings": [
                {
                    "code": finding.code,
                    "severity": finding.severity,
                    "message": finding.message,
                    "unit_index": finding.unit_index,
                    "observed_value": finding.observed_value,
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
            "execution_package_fingerprint": self.execution_package_fingerprint,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )

