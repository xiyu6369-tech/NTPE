from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Any, TypeVar

from core.book_chunking import BookChunkPlan, BookChunkPlanner
from core.book_intake import (
    BookIntakeManifest,
    BookIntakeManifestBuilder,
    BookIntakeProcessor,
    BookIntakeResult,
    BookPreflightAnalyzer,
    BookPreflightResult,
)
from core.book_segmentation import (
    BookSegmentationResult,
    BookStructureSegmenter,
)

from .errors import (
    BookPreparationBlockedError,
    BookPreparationConsistencyError,
    BookPreparationStageError,
    InvalidBookPreparationInputError,
)
from .models import BookPreparationFinding, BookPreparationResult, PreparationValue


SCHEMA_NAME = "ntpe.book_preparation"
SCHEMA_VERSION = "1.0"
STRATEGY = "deterministic_offline_book_preparation_v1"

FINDING_CODES = (
    "INTAKE_BLOCKED",
    "PREFLIGHT_BLOCKING",
    "MANUAL_REVIEW_REQUIRED",
    "INTAKE_WARNING_PROPAGATED",
    "PREFLIGHT_WARNING_PROPAGATED",
    "SEGMENTATION_WARNING_PROPAGATED",
    "CHUNKING_WARNING_PROPAGATED",
    "SOURCE_CONTENT_MISMATCH",
    "CONTENT_FINGERPRINT_MISMATCH",
    "SOURCE_NAME_MISMATCH",
    "MANIFEST_STATUS_MISMATCH",
    "SEGMENTATION_FINGERPRINT_MISMATCH",
    "CHARACTER_COUNT_MISMATCH",
    "SECTION_COUNT_MISMATCH",
    "CHUNK_COUNT_MISMATCH",
    "PIPELINE_STAGE_FAILURE",
)

FINDING_SEVERITIES = MappingProxyType(
    {
        "INTAKE_BLOCKED": "blocking",
        "PREFLIGHT_BLOCKING": "blocking",
        "MANUAL_REVIEW_REQUIRED": "manual_review",
        "INTAKE_WARNING_PROPAGATED": "warning",
        "PREFLIGHT_WARNING_PROPAGATED": "warning",
        "SEGMENTATION_WARNING_PROPAGATED": "warning",
        "CHUNKING_WARNING_PROPAGATED": "warning",
        "SOURCE_CONTENT_MISMATCH": "blocking",
        "CONTENT_FINGERPRINT_MISMATCH": "blocking",
        "SOURCE_NAME_MISMATCH": "blocking",
        "MANIFEST_STATUS_MISMATCH": "blocking",
        "SEGMENTATION_FINGERPRINT_MISMATCH": "blocking",
        "CHARACTER_COUNT_MISMATCH": "blocking",
        "SECTION_COUNT_MISMATCH": "blocking",
        "CHUNK_COUNT_MISMATCH": "blocking",
        "PIPELINE_STAGE_FAILURE": "blocking",
    }
)

_STATUS_ACTION = MappingProxyType(
    {
        "ready": "proceed",
        "ready_with_warnings": "proceed_with_warning",
        "manual_review": "manual_review",
        "blocked": "reject",
    }
)

_STATUS_NORMALIZATION = MappingProxyType(
    {
        "ready": "ready",
        "ready_with_warnings": "ready_with_warnings",
        "warning": "ready_with_warnings",
        "manual_review": "manual_review",
        "manual_review_required": "manual_review",
        "blocking": "blocked",
        "blocked": "blocked",
    }
)

_STATUS_RANK = MappingProxyType(
    {"ready": 0, "ready_with_warnings": 1, "manual_review": 2, "blocked": 3}
)

T = TypeVar("T")


class _PreparationFindingCollector:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str, PreparationValue], BookPreparationFinding] = {}

    def add(
        self,
        code: str,
        message: str,
        stage: str,
        observed_value: PreparationValue = None,
    ) -> None:
        key = (code, stage, observed_value)
        self._items.setdefault(
            key,
            BookPreparationFinding(
                code=code,
                severity=FINDING_SEVERITIES[code],
                message=message,
                stage=stage,
                observed_value=observed_value,
            ),
        )

    def ordered(self) -> tuple[BookPreparationFinding, ...]:
        code_rank = {code: index for index, code in enumerate(FINDING_CODES)}
        stage_rank = {
            "intake": 0,
            "preflight": 1,
            "manifest": 2,
            "segmentation": 3,
            "chunking": 4,
            "cross_stage": 5,
        }
        return tuple(
            sorted(
                self._items.values(),
                key=lambda item: (
                    stage_rank[item.stage],
                    code_rank[item.code],
                    "" if item.observed_value is None else str(item.observed_value),
                ),
            )
        )


class BookPreparationProcessor:
    """Run the accepted offline book pipeline once, in a fixed order."""

    def __init__(
        self,
        intake_processor: object | None = None,
        preflight_analyzer: object | None = None,
        manifest_builder: object | None = None,
        segmenter: object | None = None,
        chunk_planner: object | None = None,
    ) -> None:
        self._intake_processor = intake_processor if intake_processor is not None else BookIntakeProcessor()
        self._preflight_analyzer = preflight_analyzer if preflight_analyzer is not None else BookPreflightAnalyzer()
        self._manifest_builder = manifest_builder if manifest_builder is not None else BookIntakeManifestBuilder()
        self._segmenter = segmenter if segmenter is not None else BookStructureSegmenter()
        self._chunk_planner = chunk_planner if chunk_planner is not None else BookChunkPlanner()

    def prepare(self, source_path: str | Path) -> BookPreparationResult:
        """Run Intake once, preserving its original source exceptions."""
        intake_result = self._intake_processor.process(source_path)
        if not isinstance(intake_result, BookIntakeResult):
            raise InvalidBookPreparationInputError(
                "intake_processor must return a BookIntakeResult"
            )
        return self.prepare_intake(intake_result)

    def prepare_intake(self, intake_result: BookIntakeResult) -> BookPreparationResult:
        """Continue the fixed offline pipeline from one completed Intake result."""
        if not isinstance(intake_result, BookIntakeResult):
            raise InvalidBookPreparationInputError(
                "intake_result must be a BookIntakeResult"
            )
        if _normalize_status(intake_result.status) == "blocked":
            finding = BookPreparationFinding(
                "INTAKE_BLOCKED",
                FINDING_SEVERITIES["INTAKE_BLOCKED"],
                "Book Intake blocked preparation before downstream analysis.",
                "intake",
                intake_result.status,
            )
            raise BookPreparationBlockedError(
                "Book preparation stopped because Intake is blocked.",
                intake_result=intake_result,
                finding=finding,
            )

        preflight = self._invoke(
            "preflight", lambda: self._preflight_analyzer.analyze(intake_result)
        )
        if not isinstance(preflight, BookPreflightResult):
            raise InvalidBookPreparationInputError(
                "preflight_analyzer must return a BookPreflightResult"
            )
        if _normalize_status(preflight.status) == "blocked":
            finding = BookPreparationFinding(
                "PREFLIGHT_BLOCKING",
                FINDING_SEVERITIES["PREFLIGHT_BLOCKING"],
                "Book Preflight blocked preparation before structural analysis.",
                "preflight",
                preflight.status,
            )
            raise BookPreparationBlockedError(
                "Book preparation stopped because Preflight is blocked.",
                intake_result=intake_result,
                preflight_result=preflight,
                finding=finding,
            )

        manifest = self._invoke(
            "manifest",
            lambda: self._manifest_builder.build(intake_result, preflight),
        )
        if not isinstance(manifest, BookIntakeManifest):
            raise InvalidBookPreparationInputError(
                "manifest_builder must return a BookIntakeManifest"
            )
        segmentation = self._invoke(
            "segmentation",
            lambda: self._segmenter.segment(intake_result, manifest=manifest),
        )
        if not isinstance(segmentation, BookSegmentationResult):
            raise InvalidBookPreparationInputError(
                "segmenter must return a BookSegmentationResult"
            )
        chunk_plan = self._invoke(
            "chunking", lambda: self._chunk_planner.plan(segmentation)
        )
        if not isinstance(chunk_plan, BookChunkPlan):
            raise InvalidBookPreparationInputError(
                "chunk_planner must return a BookChunkPlan"
            )

        self._validate_consistency(
            intake_result, preflight, manifest, segmentation, chunk_plan
        )
        findings = self._aggregate_findings(
            intake_result, preflight, segmentation, chunk_plan
        )
        status = _aggregate_status(
            intake_result.status,
            preflight.status,
            segmentation.status,
            chunk_plan.status,
        )
        action = _STATUS_ACTION[status]
        source_name = _safe_name(intake_result.file_name)
        preparation_fingerprint = _preparation_fingerprint(
            source_name=source_name,
            source_content_fingerprint=manifest.content_fingerprint,
            manifest_fingerprint=manifest.manifest_fingerprint,
            segmentation_fingerprint=segmentation.segmentation_fingerprint,
            chunk_plan_fingerprint=chunk_plan.chunk_plan_fingerprint,
            status=status,
            action=action,
            findings=findings,
        )
        return BookPreparationResult(
            schema_name=SCHEMA_NAME,
            schema_version=SCHEMA_VERSION,
            strategy=STRATEGY,
            source_name=source_name,
            intake_result=intake_result,
            preflight_result=preflight,
            intake_manifest=manifest,
            segmentation_result=segmentation,
            chunk_plan=chunk_plan,
            source_content_fingerprint=manifest.content_fingerprint,
            manifest_fingerprint=manifest.manifest_fingerprint,
            segmentation_fingerprint=segmentation.segmentation_fingerprint,
            chunk_plan_fingerprint=chunk_plan.chunk_plan_fingerprint,
            status=status,
            action=action,
            findings=findings,
            summary=(
                f"Book preparation {status}: {len(segmentation.sections)} sections; "
                f"{len(chunk_plan.chunks)} translation chunks; consistency verified."
            ),
            preparation_fingerprint=preparation_fingerprint,
        )

    @staticmethod
    def _invoke(stage: str, operation: Callable[[], T]) -> T:
        try:
            return operation()
        except BookPreparationBlockedError:
            raise
        except Exception as exc:
            finding = BookPreparationFinding(
                "PIPELINE_STAGE_FAILURE",
                FINDING_SEVERITIES["PIPELINE_STAGE_FAILURE"],
                "A pipeline dependency raised an exception.",
                stage,
                exc.__class__.__name__,
            )
            raise BookPreparationStageError(stage, finding=finding) from exc

    @staticmethod
    def _validate_consistency(
        intake: BookIntakeResult,
        preflight: BookPreflightResult,
        manifest: BookIntakeManifest,
        segmentation: BookSegmentationResult,
        chunk_plan: BookChunkPlan,
    ) -> None:
        text = intake.text
        segmentation_text = segmentation.reconstruct_text()
        chunk_text = chunk_plan.reconstruct_text()
        if text != segmentation_text or text != chunk_text:
            _raise_consistency(
                "SOURCE_CONTENT_MISMATCH",
                "Completed stages do not reconstruct identical source content.",
                len(text),
            )
        actual_fingerprint = hashlib.sha256(text.encode("utf-8")).hexdigest()
        fingerprints = (
            manifest.content_fingerprint,
            segmentation.source_content_fingerprint,
            chunk_plan.source_content_fingerprint,
            actual_fingerprint,
        )
        if len(set(fingerprints)) != 1:
            _raise_consistency(
                "CONTENT_FINGERPRINT_MISMATCH",
                "Source content fingerprints are inconsistent across completed stages.",
                actual_fingerprint,
            )
        if manifest.status != preflight.status or manifest.action != preflight.recommended_action:
            _raise_consistency(
                "MANIFEST_STATUS_MISMATCH",
                "Manifest status or action does not match Preflight.",
                manifest.status,
                stage="manifest",
            )
        if chunk_plan.segmentation_fingerprint != segmentation.segmentation_fingerprint:
            _raise_consistency(
                "SEGMENTATION_FINGERPRINT_MISMATCH",
                "Chunk plan does not reference the completed segmentation fingerprint.",
                chunk_plan.segmentation_fingerprint,
            )
        names = (
            _safe_name(intake.file_name or intake.source_path.name),
            _safe_name(preflight.file_name or preflight.source_path.name),
            _safe_name(manifest.source.source_name),
            _safe_name(segmentation.source_name),
            _safe_name(chunk_plan.source_name),
        )
        if not names[0] or len(set(names)) != 1:
            _raise_consistency(
                "SOURCE_NAME_MISMATCH",
                "Source basenames are inconsistent across completed stages.",
                names[0],
            )
        if segmentation.character_count != len(text) or chunk_plan.character_count != len(text):
            _raise_consistency(
                "CHARACTER_COUNT_MISMATCH",
                "Character counts do not match the Intake text length.",
                len(text),
            )
        if chunk_plan.section_count != len(segmentation.sections):
            _raise_consistency(
                "SECTION_COUNT_MISMATCH",
                "Chunk plan section_count does not match segmentation sections.",
                chunk_plan.section_count,
            )
        if chunk_plan.chunk_count != len(chunk_plan.chunks):
            _raise_consistency(
                "CHUNK_COUNT_MISMATCH",
                "Chunk plan chunk_count does not match its chunks.",
                chunk_plan.chunk_count,
            )

    @staticmethod
    def _aggregate_findings(
        intake: BookIntakeResult,
        preflight: BookPreflightResult,
        segmentation: BookSegmentationResult,
        chunk_plan: BookChunkPlan,
    ) -> tuple[BookPreparationFinding, ...]:
        collector = _PreparationFindingCollector()
        normalized = (
            ("intake", _normalize_status(intake.status)),
            ("preflight", _normalize_status(preflight.status)),
            ("segmentation", _normalize_status(segmentation.status)),
            ("chunking", _normalize_status(chunk_plan.status)),
        )
        for stage, status in normalized:
            if status == "manual_review":
                collector.add(
                    "MANUAL_REVIEW_REQUIRED",
                    "An upstream stage requires manual review.",
                    stage,
                    status,
                )
        if normalized[0][1] == "ready_with_warnings":
            collector.add(
                "INTAKE_WARNING_PROPAGATED",
                "Book Intake completed with warnings.",
                "intake",
                _codes(intake.quality_report.findings),
            )
        if normalized[1][1] == "ready_with_warnings":
            collector.add(
                "PREFLIGHT_WARNING_PROPAGATED",
                "Book Preflight completed with warnings.",
                "preflight",
                _codes(preflight.risk_findings),
            )
        if normalized[2][1] == "ready_with_warnings":
            collector.add(
                "SEGMENTATION_WARNING_PROPAGATED",
                "Book Segmentation completed with warnings.",
                "segmentation",
                _codes(segmentation.findings),
            )
        if normalized[3][1] == "ready_with_warnings":
            collector.add(
                "CHUNKING_WARNING_PROPAGATED",
                "Book Chunk Planning completed with warnings.",
                "chunking",
                _codes(chunk_plan.findings),
            )
        return collector.ordered()


def _normalize_status(status: str) -> str:
    try:
        return _STATUS_NORMALIZATION[status]
    except KeyError as exc:
        raise BookPreparationConsistencyError(
            f"Unsupported upstream status: {status}."
        ) from exc


def _aggregate_status(*statuses: str) -> str:
    normalized = tuple(_normalize_status(status) for status in statuses)
    return max(normalized, key=lambda status: _STATUS_RANK[status])


def _safe_name(value: str) -> str:
    return PurePosixPath(PureWindowsPath(value).name).name


def _codes(findings: Any) -> str | None:
    codes = tuple(dict.fromkeys(item.code for item in findings))
    return ",".join(codes) if codes else None


def _raise_consistency(
    code: str,
    message: str,
    observed_value: PreparationValue,
    *,
    stage: str = "cross_stage",
) -> None:
    finding = BookPreparationFinding(
        code=code,
        severity=FINDING_SEVERITIES[code],
        message=message,
        stage=stage,
        observed_value=observed_value,
    )
    raise BookPreparationConsistencyError(message, finding=finding)


def _preparation_fingerprint(
    *,
    source_name: str,
    source_content_fingerprint: str,
    manifest_fingerprint: str,
    segmentation_fingerprint: str,
    chunk_plan_fingerprint: str,
    status: str,
    action: str,
    findings: tuple[BookPreparationFinding, ...],
) -> str:
    payload = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "strategy": STRATEGY,
        "source_name": source_name,
        "source_content_fingerprint": source_content_fingerprint,
        "manifest_fingerprint": manifest_fingerprint,
        "segmentation_fingerprint": segmentation_fingerprint,
        "chunk_plan_fingerprint": chunk_plan_fingerprint,
        "status": status,
        "action": action,
        "findings": [
            {
                "code": finding.code,
                "severity": finding.severity,
                "stage": finding.stage,
                "observed_value": finding.observed_value,
            }
            for finding in findings
        ],
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
