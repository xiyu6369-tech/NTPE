from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any

from .models import BookIntakeResult, BookPreflightResult


_SCHEMA_NAME = "ntpe.book_intake_manifest"
_SCHEMA_VERSION = "1.0"
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_STATUS_ACTION = {
    "ready": "proceed",
    "ready_with_warnings": "proceed_with_warning",
    "manual_review_required": "manual_review",
    "blocked": "reject",
}


class BookManifestValidationError(ValueError):
    """Raised when manifest inputs or canonical metadata are invalid."""


@dataclass(frozen=True)
class BookManifestSource:
    """Path-safe source metadata."""

    source_name: str
    source_suffix: str | None
    source_size_bytes: int | None
    source_kind: str


@dataclass(frozen=True)
class BookManifestEncoding:
    """Encoding metadata copied from the completed intake result."""

    detected_encoding: str
    confidence: float | None
    bom: str | None
    decode_status: str


@dataclass(frozen=True)
class BookManifestLanguage:
    """Language metadata copied from the completed intake result."""

    detected_language: str
    language_confidence: float | None
    script_profile: str | None


@dataclass(frozen=True)
class BookManifestCorruption:
    """Aggregate corruption metadata without source excerpts."""

    status: str
    replacement_character_count: int
    nul_character_count: int
    control_character_count: int
    finding_codes: tuple[str, ...]


@dataclass(frozen=True)
class BookManifestPreflight:
    """Preflight decision metadata with aligned immutable findings."""

    status: str
    action: str
    summary: str
    finding_codes: tuple[str, ...]
    finding_severities: tuple[str, ...]


@dataclass(frozen=True)
class BookManifestWorkload:
    """Book-scale statistics copied from the preflight result."""

    character_count: int
    non_whitespace_character_count: int
    line_count: int
    blank_line_count: int
    paragraph_count: int
    average_line_length: float
    estimated_chunk_count: int
    estimated_token_count: int
    source_chunk_size: int
    chars_per_token: float


@dataclass(frozen=True)
class BookIntakeManifest:
    """Immutable, validated, canonically serializable Book Intake manifest."""

    schema_name: str
    schema_version: str
    source: BookManifestSource
    encoding: BookManifestEncoding
    language: BookManifestLanguage
    corruption: BookManifestCorruption
    preflight: BookManifestPreflight
    workload: BookManifestWorkload
    status: str
    action: str
    content_fingerprint: str
    manifest_fingerprint: str

    def __post_init__(self) -> None:
        _validate_manifest(self)

    def to_dict(self) -> dict[str, object]:
        """Return a detached dictionary representation of this manifest."""
        return _manifest_payload(self, include_manifest_fingerprint=True)

    def to_json(self) -> str:
        """Return deterministic compact JSON with UTF-8 character semantics."""
        return _canonical_json(self.to_dict())


class BookIntakeManifestBuilder:
    """Build validated metadata from completed Intake and Preflight results."""

    def build(
        self,
        intake_result: BookIntakeResult,
        preflight_result: BookPreflightResult,
    ) -> BookIntakeManifest:
        """Build one manifest without file access or rerunning any analyzer."""
        if not isinstance(intake_result, BookIntakeResult):
            raise TypeError("intake_result must be a BookIntakeResult")
        if not isinstance(preflight_result, BookPreflightResult):
            raise TypeError("preflight_result must be a BookPreflightResult")
        _validate_source_consistency(intake_result, preflight_result)

        source_name = _safe_basename(
            intake_result.file_name or intake_result.source_path.name
        )
        source = BookManifestSource(
            source_name=source_name,
            source_suffix=PurePosixPath(source_name).suffix or None,
            source_size_bytes=intake_result.file_size_bytes,
            source_kind="text",
        )
        encoding = BookManifestEncoding(
            detected_encoding=intake_result.encoding,
            confidence=None,
            bom=None,
            decode_status="decoded",
        )
        language = BookManifestLanguage(
            detected_language=intake_result.language_result.language,
            language_confidence=_normalize_language_confidence(
                intake_result.language_result.confidence
            ),
            script_profile=intake_result.language_result.recommended_profile or None,
        )
        corruption = BookManifestCorruption(
            status=intake_result.quality_report.status,
            replacement_character_count=_finding_count(
                intake_result, "replacement_character"
            ),
            nul_character_count=_finding_count(intake_result, "null_character"),
            control_character_count=_finding_count(
                intake_result, "control_character"
            ),
            finding_codes=tuple(
                finding.code for finding in intake_result.quality_report.findings
            ),
        )
        preflight = BookManifestPreflight(
            status=preflight_result.status,
            action=preflight_result.recommended_action,
            summary=preflight_result.summary,
            finding_codes=tuple(
                finding.code for finding in preflight_result.risk_findings
            ),
            finding_severities=tuple(
                finding.severity for finding in preflight_result.risk_findings
            ),
        )
        workload = BookManifestWorkload(
            character_count=preflight_result.character_count,
            non_whitespace_character_count=(
                preflight_result.non_whitespace_character_count
            ),
            line_count=preflight_result.line_count,
            blank_line_count=(
                preflight_result.line_count - preflight_result.non_empty_line_count
            ),
            paragraph_count=preflight_result.paragraph_count,
            average_line_length=preflight_result.average_line_length,
            estimated_chunk_count=preflight_result.estimated_chunk_count,
            estimated_token_count=preflight_result.estimated_source_tokens,
            source_chunk_size=preflight_result.source_chunk_size,
            chars_per_token=preflight_result.estimated_chars_per_token,
        )
        content_fingerprint = hashlib.sha256(
            intake_result.text.encode("utf-8")
        ).hexdigest()
        payload = _parts_payload(
            source=source,
            encoding=encoding,
            language=language,
            corruption=corruption,
            preflight=preflight,
            workload=workload,
            status=preflight_result.status,
            action=preflight_result.recommended_action,
            content_fingerprint=content_fingerprint,
        )
        manifest_fingerprint = _sha256_payload(payload)
        return BookIntakeManifest(
            schema_name=_SCHEMA_NAME,
            schema_version=_SCHEMA_VERSION,
            source=source,
            encoding=encoding,
            language=language,
            corruption=corruption,
            preflight=preflight,
            workload=workload,
            status=preflight_result.status,
            action=preflight_result.recommended_action,
            content_fingerprint=content_fingerprint,
            manifest_fingerprint=manifest_fingerprint,
        )


def _safe_basename(value: str) -> str:
    return PurePosixPath(PureWindowsPath(value).name).name


def _normalize_language_confidence(value: int | float) -> float:
    numeric = float(value)
    return numeric / 100.0 if numeric > 1.0 else numeric


def _finding_count(intake_result: BookIntakeResult, code: str) -> int:
    return sum(
        finding.count
        for finding in intake_result.quality_report.findings
        if finding.code == code
    )


def _validate_source_consistency(
    intake_result: BookIntakeResult,
    preflight_result: BookPreflightResult,
) -> None:
    intake_name = _safe_basename(
        intake_result.file_name or intake_result.source_path.name
    )
    preflight_name = _safe_basename(
        preflight_result.file_name or preflight_result.source_path.name
    )
    intake_path_name = _safe_basename(str(intake_result.source_path))
    preflight_path_name = _safe_basename(str(preflight_result.source_path))
    consistent = (
        intake_name == preflight_name
        and intake_path_name == preflight_path_name
        and intake_name == intake_path_name
        and len(intake_result.text) == intake_result.text_length
        and intake_result.text_length == preflight_result.character_count
        and intake_result.encoding == preflight_result.encoding
        and intake_result.language_result.language
        == preflight_result.source_language
    )
    if not consistent:
        raise BookManifestValidationError(
            "Intake and preflight results do not describe the same source."
        )


def _parts_payload(
    *,
    source: BookManifestSource,
    encoding: BookManifestEncoding,
    language: BookManifestLanguage,
    corruption: BookManifestCorruption,
    preflight: BookManifestPreflight,
    workload: BookManifestWorkload,
    status: str,
    action: str,
    content_fingerprint: str,
) -> dict[str, object]:
    return {
        "schema_name": _SCHEMA_NAME,
        "schema_version": _SCHEMA_VERSION,
        "source": asdict(source),
        "encoding": asdict(encoding),
        "language": asdict(language),
        "corruption": asdict(corruption),
        "preflight": asdict(preflight),
        "workload": asdict(workload),
        "status": status,
        "action": action,
        "content_fingerprint": content_fingerprint,
    }


def _manifest_payload(
    manifest: BookIntakeManifest,
    *,
    include_manifest_fingerprint: bool,
) -> dict[str, object]:
    payload = {
        "schema_name": manifest.schema_name,
        "schema_version": manifest.schema_version,
        "source": asdict(manifest.source),
        "encoding": asdict(manifest.encoding),
        "language": asdict(manifest.language),
        "corruption": asdict(manifest.corruption),
        "preflight": asdict(manifest.preflight),
        "workload": asdict(manifest.workload),
        "status": manifest.status,
        "action": manifest.action,
        "content_fingerprint": manifest.content_fingerprint,
    }
    if include_manifest_fingerprint:
        payload["manifest_fingerprint"] = manifest.manifest_fingerprint
    return payload


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_payload(payload: dict[str, object]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _validate_manifest(manifest: BookIntakeManifest) -> None:
    if manifest.schema_name != _SCHEMA_NAME:
        raise BookManifestValidationError("Invalid manifest schema_name.")
    if manifest.schema_version != _SCHEMA_VERSION:
        raise BookManifestValidationError("Invalid manifest schema_version.")
    for name, value in (
        ("content_fingerprint", manifest.content_fingerprint),
        ("manifest_fingerprint", manifest.manifest_fingerprint),
    ):
        if not _HEX_64.fullmatch(value):
            raise BookManifestValidationError(f"Invalid {name}.")
    expected_fingerprint = _sha256_payload(
        _manifest_payload(manifest, include_manifest_fingerprint=False)
    )
    if manifest.manifest_fingerprint != expected_fingerprint:
        raise BookManifestValidationError(
            "Manifest fingerprint does not match payload."
        )

    _validate_source(manifest.source)
    _validate_confidence(manifest.encoding.confidence, "encoding confidence")
    _validate_confidence(
        manifest.language.language_confidence, "language confidence"
    )
    if manifest.status not in _STATUS_ACTION:
        raise BookManifestValidationError("Invalid manifest status.")
    if manifest.action not in _STATUS_ACTION.values():
        raise BookManifestValidationError("Invalid manifest action.")
    if _STATUS_ACTION[manifest.status] != manifest.action:
        raise BookManifestValidationError("Invalid status/action combination.")
    if manifest.preflight.status != manifest.status:
        raise BookManifestValidationError("Preflight status does not match manifest.")
    if manifest.preflight.action != manifest.action:
        raise BookManifestValidationError("Preflight action does not match manifest.")

    _validate_codes(manifest.corruption.finding_codes, "corruption")
    _validate_codes(manifest.preflight.finding_codes, "preflight")
    if len(manifest.preflight.finding_codes) != len(
        manifest.preflight.finding_severities
    ):
        raise BookManifestValidationError(
            "Preflight finding codes and severities must align."
        )
    if any(not severity for severity in manifest.preflight.finding_severities):
        raise BookManifestValidationError("Preflight severity cannot be empty.")

    for name, value in (
        ("source_size_bytes", manifest.source.source_size_bytes),
        (
            "replacement_character_count",
            manifest.corruption.replacement_character_count,
        ),
        ("nul_character_count", manifest.corruption.nul_character_count),
        ("control_character_count", manifest.corruption.control_character_count),
        ("character_count", manifest.workload.character_count),
        (
            "non_whitespace_character_count",
            manifest.workload.non_whitespace_character_count,
        ),
        ("line_count", manifest.workload.line_count),
        ("blank_line_count", manifest.workload.blank_line_count),
        ("paragraph_count", manifest.workload.paragraph_count),
        ("average_line_length", manifest.workload.average_line_length),
        ("estimated_chunk_count", manifest.workload.estimated_chunk_count),
        ("estimated_token_count", manifest.workload.estimated_token_count),
    ):
        if value is not None and value < 0:
            raise BookManifestValidationError(f"{name} cannot be negative.")
    if manifest.workload.source_chunk_size <= 0:
        raise BookManifestValidationError("source_chunk_size must be positive.")
    if (
        not math.isfinite(manifest.workload.chars_per_token)
        or manifest.workload.chars_per_token <= 0
    ):
        raise BookManifestValidationError("chars_per_token must be positive.")

    if _contains_absolute_path(
        _manifest_payload(manifest, include_manifest_fingerprint=True)
    ):
        raise BookManifestValidationError(
            "Manifest cannot contain an absolute path."
        )


def _validate_source(source: BookManifestSource) -> None:
    if not source.source_name:
        raise BookManifestValidationError("source_name cannot be empty.")
    if (
        source.source_name != PureWindowsPath(source.source_name).name
        or source.source_name != PurePosixPath(source.source_name).name
        or PureWindowsPath(source.source_name).is_absolute()
        or PurePosixPath(source.source_name).is_absolute()
    ):
        raise BookManifestValidationError("source_name must be a basename.")


def _validate_confidence(value: float | None, name: str) -> None:
    if value is not None and (
        not math.isfinite(value) or value < 0.0 or value > 1.0
    ):
        raise BookManifestValidationError(
            f"{name} must be between 0.0 and 1.0."
        )


def _validate_codes(codes: tuple[str, ...], section: str) -> None:
    if any(not code for code in codes):
        raise BookManifestValidationError(
            f"{section} finding code cannot be empty."
        )


def _contains_absolute_path(value: Any) -> bool:
    if isinstance(value, str):
        return (
            PureWindowsPath(value).is_absolute()
            or PurePosixPath(value).is_absolute()
        )
    if isinstance(value, dict):
        return any(_contains_absolute_path(item) for item in value.values())
    if isinstance(value, (tuple, list)):
        return any(_contains_absolute_path(item) for item in value)
    return False