from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path, PurePosixPath
from typing import Any


_COMPONENT_NAME = "ntpe.book_preparation_pipeline"
_FREEZE_VERSION = "3.4"
_SCHEMA_NAME = "ntpe.book_preparation"
_SCHEMA_VERSION = "1.0"
_STRATEGY = "deterministic_offline_book_preparation_v1"
_ACTIVATION_GATE = "book_preparation_pipeline_frozen"
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")

_FROZEN_MODULES = (
    "core/book_chunking/__init__.py",
    "core/book_chunking/errors.py",
    "core/book_chunking/models.py",
    "core/book_chunking/planner.py",
    "core/book_chunking/policy.py",
    "core/book_preparation/__init__.py",
    "core/book_preparation/errors.py",
    "core/book_preparation/freeze.py",
    "core/book_preparation/models.py",
    "core/book_preparation/processor.py",
    "core/book_segmentation/__init__.py",
    "core/book_segmentation/errors.py",
    "core/book_segmentation/models.py",
    "core/book_segmentation/policy.py",
    "core/book_segmentation/segmenter.py",
)

_SEGMENTATION_API = (
    "BookStructureSegmenter",
    "BookSegmentationResult",
    "BookSection",
    "ChapterHeading",
    "SegmentationFinding",
    "BookSegmentationError",
    "InvalidSegmentationInputError",
    "SegmentationInvariantError",
    "SourceFingerprintMismatchError",
)

_CHUNKING_API = (
    "BookChunkPlanner",
    "BookChunkPlan",
    "TranslationChunk",
    "ChunkBoundary",
    "ChunkPlanningFinding",
    "BookChunkingError",
    "InvalidChunkPolicyError",
    "ChunkPlanningInvariantError",
    "SegmentationConsistencyError",
)

_PREPARATION_API = (
    "BookPreparationProcessor",
    "BookPreparationResult",
    "BookPreparationFinding",
    "BookPreparationError",
    "BookPreparationConsistencyError",
    "BookPreparationBlockedError",
    "BookPreparationStageError",
    "InvalidBookPreparationInputError",
    "BookPreparationFreezeMetadata",
    "BookPreparationFreezeValidationResult",
    "BookPreparationFreezeValidationError",
    "get_book_preparation_freeze_metadata",
    "validate_book_preparation_freeze",
)

_PUBLIC_API = _SEGMENTATION_API + _CHUNKING_API + _PREPARATION_API

_INVARIANTS = (
    "offline_only",
    "deterministic",
    "immutable_results",
    "source_content_preserved",
    "unicode_text_preserved",
    "newline_style_preserved",
    "whitespace_preserved",
    "segmentation_offsets_half_open",
    "segmentation_offsets_gap_free",
    "segmentation_offsets_non_overlapping",
    "segmentation_reconstruction_exact",
    "chapter_heading_detection_conservative",
    "numeric_heading_detection_requires_sequence",
    "front_matter_preserved",
    "no_heading_results_in_manual_review",
    "chunk_offsets_gap_free",
    "chunk_offsets_non_overlapping",
    "chunk_reconstruction_exact",
    "chunk_maximum_size_enforced",
    "chunk_boundary_priority_frozen",
    "chapter_heading_not_split",
    "hard_split_last_resort",
    "crlf_not_split",
    "pipeline_execution_order_frozen",
    "each_stage_invoked_once",
    "cross_stage_content_consistency_fail_closed",
    "cross_stage_fingerprint_consistency_fail_closed",
    "upstream_blocking_stops_pipeline",
    "manual_review_not_downgraded",
    "status_action_mapping_frozen",
    "no_provider_execution",
    "no_network_execution",
    "no_translation_execution",
    "no_output_file_write",
    "no_runtime_integration",
    "no_launcher_integration",
    "no_production_hook",
)

_RESULT_FIELDS = (
    "schema_name",
    "schema_version",
    "strategy",
    "source_name",
    "intake_result",
    "preflight_result",
    "intake_manifest",
    "segmentation_result",
    "chunk_plan",
    "source_content_fingerprint",
    "manifest_fingerprint",
    "segmentation_fingerprint",
    "chunk_plan_fingerprint",
    "status",
    "action",
    "findings",
    "summary",
    "preparation_fingerprint",
)

_STATUS_ACTION = {
    "ready": "proceed",
    "ready_with_warnings": "proceed_with_warning",
    "manual_review": "manual_review",
    "blocked": "reject",
}

_STATUS_PRIORITY = (
    "blocked",
    "manual_review",
    "ready_with_warnings",
    "ready",
)

_BOUNDARY_PRIORITY = ("paragraph", "sentence", "line", "hard_limit")
_CHUNK_SIZES = {"minimum": 800, "target": 2000, "maximum": 2600}
_MANIFEST_RELATIVE_PATH = Path(
    "manifests/book_preparation_stage34_freeze_manifest.json"
)


class BookPreparationFreezeValidationError(RuntimeError):
    """Raised when the Stage 3.4 frozen pipeline baseline drifts."""


@dataclass(frozen=True)
class BookPreparationFreezeMetadata:
    component_name: str
    freeze_version: str
    schema_name: str
    schema_version: str
    strategy: str
    activation_gate: str
    frozen_modules: tuple[str, ...]
    public_api: tuple[str, ...]
    invariants: tuple[str, ...]
    production_integration_authorized: bool
    translation_runtime_integration_authorized: bool
    provider_execution_authorized: bool
    automatic_translation_authorized: bool


@dataclass(frozen=True)
class BookPreparationFreezeValidationResult:
    valid: bool
    component_name: str
    freeze_version: str
    checked_source_count: int
    public_api_count: int
    invariant_count: int
    hash_drift_count: int
    activation_gate: str
    summary: str


_METADATA = BookPreparationFreezeMetadata(
    component_name=_COMPONENT_NAME,
    freeze_version=_FREEZE_VERSION,
    schema_name=_SCHEMA_NAME,
    schema_version=_SCHEMA_VERSION,
    strategy=_STRATEGY,
    activation_gate=_ACTIVATION_GATE,
    frozen_modules=_FROZEN_MODULES,
    public_api=_PUBLIC_API,
    invariants=_INVARIANTS,
    production_integration_authorized=False,
    translation_runtime_integration_authorized=False,
    provider_execution_authorized=False,
    automatic_translation_authorized=False,
)


def get_book_preparation_freeze_metadata() -> BookPreparationFreezeMetadata:
    """Return the immutable, environment-free Stage 3.4 freeze metadata."""
    return _METADATA


def validate_book_preparation_freeze() -> BookPreparationFreezeValidationResult:
    """Fail closed on manifest, API, schema, policy, or frozen-source drift."""
    try:
        repository_root = Path(__file__).resolve().parents[2]
        manifest_path = repository_root / _MANIFEST_RELATIVE_PATH
        raw_manifest = manifest_path.read_bytes()
        if raw_manifest.startswith(b"\xef\xbb\xbf"):
            raise BookPreparationFreezeValidationError(
                "Freeze manifest must not contain a BOM."
            )
        manifest_text = raw_manifest.decode("utf-8")
        manifest = json.loads(manifest_text)
        canonical = json.dumps(
            manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        if manifest_text not in {canonical, canonical + "\n"}:
            raise BookPreparationFreezeValidationError(
                "Freeze manifest is not canonical JSON."
            )
        _validate_manifest_contract(manifest)
        _validate_public_api()
        _validate_source_inventory(repository_root, manifest)
        _validate_schema_and_policy_contracts()
        return BookPreparationFreezeValidationResult(
            valid=True,
            component_name=_COMPONENT_NAME,
            freeze_version=_FREEZE_VERSION,
            checked_source_count=len(_FROZEN_MODULES),
            public_api_count=len(_PUBLIC_API),
            invariant_count=len(_INVARIANTS),
            hash_drift_count=0,
            activation_gate=_ACTIVATION_GATE,
            summary="Book preparation pipeline freeze validation passed.",
        )
    except BookPreparationFreezeValidationError:
        raise
    except Exception as exc:
        raise BookPreparationFreezeValidationError(
            f"Book preparation freeze validation failed: {exc}"
        ) from exc


def _validate_manifest_contract(manifest: dict[str, Any]) -> None:
    expected_scalars = {
        "component": _COMPONENT_NAME,
        "stage": _FREEZE_VERSION,
        "freeze_version": _FREEZE_VERSION,
        "schema_name": _SCHEMA_NAME,
        "schema_version": _SCHEMA_VERSION,
        "strategy": _STRATEGY,
        "activation_gate": _ACTIVATION_GATE,
        "provider_requests_added": 0,
        "network_requests_added": 0,
        "translation_executions_added": 0,
        "output_file_writes_added": 0,
        "runtime_integrations_added": 0,
        "launcher_integrations_added": 0,
        "production_hooks_added": 0,
        "production_integration_authorized": False,
        "translation_runtime_integration_authorized": False,
        "provider_execution_authorized": False,
        "automatic_translation_authorized": False,
    }
    for key, expected in expected_scalars.items():
        if manifest.get(key) != expected:
            raise BookPreparationFreezeValidationError(
                f"Invalid freeze manifest field: {key}."
            )
    tuple_contracts = (
        ("public_api", _PUBLIC_API),
        ("invariants", _INVARIANTS),
        ("result_fields", _RESULT_FIELDS),
        ("status_priority", _STATUS_PRIORITY),
        ("boundary_priority", _BOUNDARY_PRIORITY),
    )
    for name, expected in tuple_contracts:
        if tuple(manifest.get(name, ())) != expected:
            raise BookPreparationFreezeValidationError(
                f"Frozen manifest contract drifted: {name}."
            )
    if manifest.get("status_action") != _STATUS_ACTION:
        raise BookPreparationFreezeValidationError(
            "Frozen status/action manifest contract drifted."
        )
    if manifest.get("chunk_sizes") != _CHUNK_SIZES:
        raise BookPreparationFreezeValidationError(
            "Frozen chunk size manifest contract drifted."
        )
    tests = manifest.get("validation_tests")
    if not isinstance(tests, list) or not tests or len(tests) != len(set(tests)):
        raise BookPreparationFreezeValidationError(
            "Validation test inventory is invalid."
        )


def _validate_public_api() -> None:
    import core.book_chunking as chunking
    import core.book_preparation as preparation
    import core.book_segmentation as segmentation

    packages = (
        (segmentation, _SEGMENTATION_API, "core.book_segmentation"),
        (chunking, _CHUNKING_API, "core.book_chunking"),
        (preparation, _PREPARATION_API, "core.book_preparation"),
    )
    if len(_PUBLIC_API) != len(set(_PUBLIC_API)):
        raise BookPreparationFreezeValidationError(
            "Duplicate frozen public API name detected."
        )
    for package, expected, module_prefix in packages:
        exports = tuple(package.__all__)
        if exports != expected:
            raise BookPreparationFreezeValidationError(
                f"Public API inventory drifted: {module_prefix}."
            )
        for name in exports:
            if not name or name.startswith("_"):
                raise BookPreparationFreezeValidationError(
                    "Private or empty public API name detected."
                )
            value = getattr(package, name, None)
            if value is None:
                raise BookPreparationFreezeValidationError(
                    f"Missing public API export: {name}."
                )
            owner = getattr(value, "__module__", "")
            if owner and not owner.startswith(module_prefix):
                raise BookPreparationFreezeValidationError(
                    f"Public API symbol has an invalid owner: {name}."
                )


def _validate_source_inventory(
    repository_root: Path, manifest: dict[str, Any]
) -> None:
    entries = manifest.get("frozen_files")
    if not isinstance(entries, list):
        raise BookPreparationFreezeValidationError(
            "Frozen source inventory is missing."
        )
    paths = [entry.get("path") for entry in entries if isinstance(entry, dict)]
    if len(paths) != len(entries) or len(paths) != len(set(paths)):
        raise BookPreparationFreezeValidationError(
            "Duplicate or invalid frozen source path."
        )
    if paths != sorted(paths) or tuple(paths) != _FROZEN_MODULES:
        raise BookPreparationFreezeValidationError(
            "Frozen source inventory is incomplete, extra, or unsorted."
        )
    discovered = tuple(
        sorted(
            path.relative_to(repository_root).as_posix()
            for package_name in (
                "book_segmentation",
                "book_chunking",
                "book_preparation",
            )
            for path in (repository_root / "core" / package_name).glob("*.py")
        )
    )
    if discovered != _FROZEN_MODULES:
        raise BookPreparationFreezeValidationError(
            "Formal Stage 3 source inventory drifted."
        )
    allowed_prefixes = (
        "core/book_segmentation/",
        "core/book_chunking/",
        "core/book_preparation/",
    )
    for entry in entries:
        relative = entry["path"]
        pure_path = PurePosixPath(relative)
        if (
            pure_path.is_absolute()
            or ".." in pure_path.parts
            or not relative.startswith(allowed_prefixes)
            or not relative.endswith(".py")
            or "__pycache__" in pure_path.parts
        ):
            raise BookPreparationFreezeValidationError(
                f"Invalid frozen source path: {relative}."
            )
        expected_hash = entry.get("sha256")
        if not isinstance(expected_hash, str) or not _HEX_64.fullmatch(expected_hash):
            raise BookPreparationFreezeValidationError(
                f"Invalid frozen SHA-256: {relative}."
            )
        source_path = repository_root.joinpath(*pure_path.parts)
        if not source_path.is_file():
            raise BookPreparationFreezeValidationError(
                f"Frozen source file is missing: {relative}."
            )
        observed_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if observed_hash != expected_hash:
            raise BookPreparationFreezeValidationError(
                f"Frozen source hash mismatch: {relative}."
            )


def _validate_schema_and_policy_contracts() -> None:
    from core.book_chunking.policy import DEFAULT_POLICY as chunk_policy
    from core.book_preparation.models import (
        BookPreparationFinding,
        BookPreparationResult,
    )
    from core.book_preparation import processor

    if (
        processor.SCHEMA_NAME != _SCHEMA_NAME
        or processor.SCHEMA_VERSION != _SCHEMA_VERSION
        or processor.STRATEGY != _STRATEGY
    ):
        raise BookPreparationFreezeValidationError(
            "Book preparation schema or strategy drifted."
        )
    if tuple(field.name for field in fields(BookPreparationResult)) != _RESULT_FIELDS:
        raise BookPreparationFreezeValidationError(
            "BookPreparationResult field contract drifted."
        )
    models = (BookPreparationResult, BookPreparationFinding)
    if any(
        not is_dataclass(model) or not model.__dataclass_params__.frozen
        for model in models
    ):
        raise BookPreparationFreezeValidationError(
            "Book preparation model immutability drifted."
        )
    if dict(processor._STATUS_ACTION) != _STATUS_ACTION:
        raise BookPreparationFreezeValidationError(
            "Book preparation status/action mapping drifted."
        )
    observed_priority = tuple(
        status
        for status, _ in sorted(
            processor._STATUS_RANK.items(), key=lambda item: item[1], reverse=True
        )
    )
    if observed_priority != _STATUS_PRIORITY:
        raise BookPreparationFreezeValidationError(
            "Book preparation status priority drifted."
        )
    if (
        chunk_policy.minimum_chunk_size != _CHUNK_SIZES["minimum"]
        or chunk_policy.target_chunk_size != _CHUNK_SIZES["target"]
        or chunk_policy.maximum_chunk_size != _CHUNK_SIZES["maximum"]
        or chunk_policy.boundary_priority != _BOUNDARY_PRIORITY
    ):
        raise BookPreparationFreezeValidationError(
            "Book chunking default policy drifted."
        )
