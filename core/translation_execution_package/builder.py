from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import PurePosixPath, PureWindowsPath

from core.book_intake import get_book_intake_freeze_metadata
from core.book_preparation import (
    BookPreparationResult,
    get_book_preparation_freeze_metadata,
)

from .errors import (
    ExecutionPackageConsistencyError,
    ExecutionPackageInvariantError,
    InvalidExecutionPackageInputError,
    InvalidPreparationStateError,
)
from .models import (
    ExecutionPackageFinding,
    ExecutionSourceReference,
    TranslationExecutionPackage,
    TranslationExecutionUnit,
)
from .policy import DEFAULT_POLICY, ExecutionPackagePolicy, make_unit_id


class _FindingCollector:
    def __init__(self, policy: ExecutionPackagePolicy) -> None:
        self._policy = policy
        self._items: dict[
            tuple[str, int | None, str | int | float | bool | None],
            ExecutionPackageFinding,
        ] = {}

    def add(
        self,
        code: str,
        *,
        unit_index: int | None = None,
        observed_value: str | int | float | bool | None = None,
    ) -> None:
        key = (code, unit_index, observed_value)
        self._items.setdefault(
            key,
            ExecutionPackageFinding(
                code=code,
                severity=self._policy.finding_severities[code],
                message=self._policy.finding_messages[code],
                unit_index=unit_index,
                observed_value=observed_value,
            ),
        )

    def ordered(self) -> tuple[ExecutionPackageFinding, ...]:
        return tuple(
            sorted(
                self._items.values(),
                key=lambda item: (
                    self._policy.finding_order[item.code],
                    -1 if item.unit_index is None else item.unit_index,
                    "" if item.observed_value is None else str(item.observed_value),
                ),
            )
        )


class TranslationExecutionPackageBuilder:
    """Map one frozen preparation result into an offline, non-executable package."""

    def __init__(self, policy: ExecutionPackagePolicy = DEFAULT_POLICY) -> None:
        if not isinstance(policy, ExecutionPackagePolicy):
            raise InvalidExecutionPackageInputError(
                "policy must be an ExecutionPackagePolicy"
            )
        self._policy = policy

    def build(self, preparation_result: BookPreparationResult) -> TranslationExecutionPackage:
        if not isinstance(preparation_result, BookPreparationResult):
            raise InvalidExecutionPackageInputError(
                "preparation_result must be a BookPreparationResult"
            )
        self._validate_activation_gates()
        self._validate_state(preparation_result)
        source_text = preparation_result.intake_result.text
        self._validate_cross_stage(preparation_result, source_text)
        units = self._map_units(preparation_result, source_text)
        if not units:
            self._raise_consistency("EMPTY_EXECUTION_PACKAGE", observed_value=0)

        findings = _FindingCollector(self._policy)
        if preparation_result.status == "ready_with_warnings":
            warning_codes = tuple(
                dict.fromkeys(
                    finding.code
                    for finding in preparation_result.findings
                    if finding.severity == "warning"
                )
            )
            findings.add(
                "PREPARATION_WARNING_PROPAGATED",
                observed_value=",".join(warning_codes) if warning_codes else "ready_with_warnings",
            )
        findings.add("EXECUTION_NOT_AUTHORIZED")
        ordered_findings = findings.ordered()

        status = self._policy.preparation_status_map[preparation_result.status]
        action = self._policy.status_actions[status]
        source = ExecutionSourceReference(
            source_name=_safe_name(preparation_result.source_name),
            source_content_fingerprint=preparation_result.source_content_fingerprint,
            manifest_fingerprint=preparation_result.manifest_fingerprint,
            segmentation_fingerprint=preparation_result.segmentation_fingerprint,
            chunk_plan_fingerprint=preparation_result.chunk_plan_fingerprint,
            preparation_fingerprint=preparation_result.preparation_fingerprint,
        )
        character_count = len(source_text)
        covered_character_count = sum(unit.character_count for unit in units)
        coverage_ratio = covered_character_count / character_count
        package_fingerprint = self._package_fingerprint(
            source=source,
            units=units,
            status=status,
            action=action,
            findings=ordered_findings,
            unit_count=len(units),
            character_count=character_count,
            covered_character_count=covered_character_count,
            coverage_ratio=coverage_ratio,
        )
        package = TranslationExecutionPackage(
            schema_name=self._policy.schema_name,
            schema_version=self._policy.schema_version,
            strategy=self._policy.strategy,
            activation_gate=self._policy.activation_gate,
            source=source,
            units=units,
            unit_count=len(units),
            character_count=character_count,
            covered_character_count=covered_character_count,
            coverage_ratio=coverage_ratio,
            status=status,
            action=action,
            findings=ordered_findings,
            summary=(
                f"Translation execution package {status}: {len(units)} units; "
                "source coverage verified; execution authorization withheld."
            ),
            **self._policy.authorization_flags,
            execution_package_fingerprint=package_fingerprint,
        )
        if package.reconstruct_source_text() != source_text:
            raise ExecutionPackageInvariantError(
                "Materialized package does not reconstruct the prepared source."
            )
        return package

    def _validate_activation_gates(self) -> None:
        observed = (
            get_book_intake_freeze_metadata().activation_gate,
            get_book_preparation_freeze_metadata().activation_gate,
        )
        if observed != self._policy.required_activation_gates:
            raise ExecutionPackageConsistencyError(
                "Required frozen activation gates are not satisfied."
            )

    def _validate_state(self, preparation: BookPreparationResult) -> None:
        if preparation.status in self._policy.allowed_preparation_states:
            return
        if preparation.status == "manual_review":
            code = "PREPARATION_MANUAL_REVIEW_REJECTED"
        elif preparation.status == "blocked":
            code = "PREPARATION_BLOCKED_REJECTED"
        else:
            code = "PREPARATION_BLOCKED_REJECTED"
        action = self._policy.rejected_preparation_actions.get(
            preparation.status, "reject"
        )
        finding_codes = tuple(
            dict.fromkeys((code, *(finding.code for finding in preparation.findings)))
        )
        raise InvalidPreparationStateError(
            f"Preparation status {preparation.status!r} cannot produce an execution package.",
            preparation_status=preparation.status,
            action=action,
            finding_codes=finding_codes,
        )

    def _validate_cross_stage(
        self, preparation: BookPreparationResult, source_text: str
    ) -> None:
        if not source_text:
            self._raise_consistency("EMPTY_EXECUTION_PACKAGE", observed_value=0)
        actual_source_fingerprint = _sha256_text(source_text)
        source_fingerprints = (
            preparation.source_content_fingerprint,
            preparation.intake_manifest.content_fingerprint,
            preparation.segmentation_result.source_content_fingerprint,
            preparation.chunk_plan.source_content_fingerprint,
            _sha256_text(preparation.intake_result.text),
            actual_source_fingerprint,
        )
        if len(set(source_fingerprints)) != 1:
            self._raise_consistency(
                "SOURCE_FINGERPRINT_MISMATCH",
                observed_value=actual_source_fingerprint,
            )
        if preparation.manifest_fingerprint != preparation.intake_manifest.manifest_fingerprint:
            self._raise_consistency(
                "MANIFEST_FINGERPRINT_MISMATCH",
                observed_value=preparation.manifest_fingerprint,
            )
        if preparation.segmentation_fingerprint != preparation.segmentation_result.segmentation_fingerprint:
            self._raise_consistency(
                "SEGMENTATION_FINGERPRINT_MISMATCH",
                observed_value=preparation.segmentation_fingerprint,
            )
        if preparation.chunk_plan_fingerprint != preparation.chunk_plan.chunk_plan_fingerprint:
            self._raise_consistency(
                "CHUNK_PLAN_FINGERPRINT_MISMATCH",
                observed_value=preparation.chunk_plan_fingerprint,
            )
        expected_preparation_fingerprint = _preparation_fingerprint(preparation)
        if preparation.preparation_fingerprint != expected_preparation_fingerprint:
            self._raise_consistency(
                "PREPARATION_FINGERPRINT_MISMATCH",
                observed_value=preparation.preparation_fingerprint,
            )
        if preparation.chunk_plan.chunk_count != len(preparation.chunk_plan.chunks):
            self._raise_consistency(
                "UNIT_COUNT_MISMATCH",
                observed_value=preparation.chunk_plan.chunk_count,
            )
        if preparation.chunk_plan.character_count != len(source_text):
            self._raise_consistency(
                "RECONSTRUCTION_MISMATCH",
                observed_value=preparation.chunk_plan.character_count,
            )

    def _map_units(
        self, preparation: BookPreparationResult, source_text: str
    ) -> tuple[TranslationExecutionUnit, ...]:
        output: list[TranslationExecutionUnit] = []
        expected_start = 0
        sections = preparation.segmentation_result.sections
        for index, chunk in enumerate(preparation.chunk_plan.chunks):
            if chunk.index != index:
                self._raise_consistency(
                    "UNIT_INDEX_MISMATCH", unit_index=index, observed_value=chunk.index
                )
            if chunk.source_character_start > expected_start:
                self._raise_consistency(
                    "UNIT_OFFSET_GAP",
                    unit_index=index,
                    observed_value=chunk.source_character_start,
                )
            if chunk.source_character_start < expected_start:
                self._raise_consistency(
                    "UNIT_OFFSET_OVERLAP",
                    unit_index=index,
                    observed_value=chunk.source_character_start,
                )
            if chunk.source_character_end < chunk.source_character_start:
                self._raise_consistency(
                    "UNIT_OFFSET_OVERLAP",
                    unit_index=index,
                    observed_value=chunk.source_character_end,
                )
            source_slice = source_text[
                chunk.source_character_start : chunk.source_character_end
            ]
            if chunk.text != source_slice or chunk.character_count != len(chunk.text):
                self._raise_consistency(
                    "UNIT_TEXT_MISMATCH", unit_index=index
                )
            expected_sections = tuple(
                section.index
                for section in sections
                if section.character_start < chunk.source_character_end
                and section.character_end > chunk.source_character_start
            )
            if chunk.section_indices != expected_sections:
                self._raise_consistency(
                    "UNIT_SECTION_REFERENCE_MISMATCH",
                    unit_index=index,
                    observed_value=",".join(map(str, chunk.section_indices)),
                )
            actual_chunk_fingerprint = _sha256_text(chunk.text)
            if chunk.content_fingerprint != actual_chunk_fingerprint:
                self._raise_consistency(
                    "CHUNK_FINGERPRINT_MISMATCH",
                    unit_index=index,
                    observed_value=chunk.content_fingerprint,
                )
            unit_id = make_unit_id(index, chunk.content_fingerprint)
            fingerprint_payload = {
                "index": index,
                "unit_id": unit_id,
                "chunk_index": chunk.index,
                "source_character_start": chunk.source_character_start,
                "source_character_end": chunk.source_character_end,
                "section_indices": list(chunk.section_indices),
                "heading_text": chunk.heading_text,
                "boundary_reason": chunk.boundary_reason,
                "source_chunk_fingerprint": chunk.content_fingerprint,
                "status": self._policy.unit_status,
                "attempt_count": self._policy.unit_attempt_count,
                "provider_request_count": self._policy.unit_provider_request_count,
                "translation_result_attached": self._policy.unit_translation_result_attached,
            }
            unit_fingerprint = _sha256_payload(fingerprint_payload)
            output.append(
                TranslationExecutionUnit(
                    index=index,
                    unit_id=unit_id,
                    chunk_index=chunk.index,
                    text=chunk.text,
                    source_character_start=chunk.source_character_start,
                    source_character_end=chunk.source_character_end,
                    section_indices=chunk.section_indices,
                    heading_text=chunk.heading_text,
                    boundary_reason=chunk.boundary_reason,
                    character_count=chunk.character_count,
                    non_whitespace_character_count=chunk.non_whitespace_character_count,
                    source_chunk_fingerprint=chunk.content_fingerprint,
                    execution_unit_fingerprint=unit_fingerprint,
                    status=self._policy.unit_status,
                    attempt_count=self._policy.unit_attempt_count,
                    provider_request_count=self._policy.unit_provider_request_count,
                    translation_result_attached=self._policy.unit_translation_result_attached,
                )
            )
            expected_start = chunk.source_character_end
        if expected_start != len(source_text):
            self._raise_consistency(
                "UNIT_OFFSET_GAP", observed_value=expected_start
            )
        units = tuple(output)
        if "".join(unit.text for unit in units) != source_text:
            self._raise_consistency("RECONSTRUCTION_MISMATCH")
        return units

    def _package_fingerprint(
        self,
        *,
        source: ExecutionSourceReference,
        units: tuple[TranslationExecutionUnit, ...],
        status: str,
        action: str,
        findings: tuple[ExecutionPackageFinding, ...],
        unit_count: int,
        character_count: int,
        covered_character_count: int,
        coverage_ratio: float,
    ) -> str:
        payload = {
            "schema_name": self._policy.schema_name,
            "schema_version": self._policy.schema_version,
            "strategy": self._policy.strategy,
            "activation_gate": self._policy.activation_gate,
            "source": asdict(source),
            "unit_fingerprints": [
                unit.execution_unit_fingerprint for unit in units
            ],
            "status": status,
            "action": action,
            "findings": [asdict(finding) for finding in findings],
            "authorization_flags": dict(self._policy.authorization_flags),
            "unit_count": unit_count,
            "character_count": character_count,
            "covered_character_count": covered_character_count,
            "coverage_ratio": coverage_ratio,
        }
        return _sha256_payload(payload)

    def _raise_consistency(
        self,
        code: str,
        *,
        unit_index: int | None = None,
        observed_value: str | int | float | bool | None = None,
    ) -> None:
        finding = ExecutionPackageFinding(
            code=code,
            severity=self._policy.finding_severities[code],
            message=self._policy.finding_messages[code],
            unit_index=unit_index,
            observed_value=observed_value,
        )
        raise ExecutionPackageConsistencyError(finding.message, finding=finding)


def _safe_name(value: str) -> str:
    return PurePosixPath(PureWindowsPath(value).name).name


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _sha256_payload(payload: object) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _preparation_fingerprint(preparation: BookPreparationResult) -> str:
    payload = {
        "schema_name": preparation.schema_name,
        "schema_version": preparation.schema_version,
        "strategy": preparation.strategy,
        "source_name": preparation.source_name,
        "source_content_fingerprint": preparation.source_content_fingerprint,
        "manifest_fingerprint": preparation.manifest_fingerprint,
        "segmentation_fingerprint": preparation.segmentation_fingerprint,
        "chunk_plan_fingerprint": preparation.chunk_plan_fingerprint,
        "status": preparation.status,
        "action": preparation.action,
        "findings": [
            {
                "code": finding.code,
                "severity": finding.severity,
                "stage": finding.stage,
                "observed_value": finding.observed_value,
            }
            for finding in preparation.findings
        ],
    }
    return _sha256_payload(payload)

