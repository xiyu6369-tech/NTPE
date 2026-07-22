from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path, PurePosixPath
from typing import Any

_COMPONENT_NAME = "ntpe.book_intake"
_FREEZE_VERSION = "2.8"
_SCHEMA_NAME = "ntpe.book_intake_manifest"
_SCHEMA_VERSION = "1.0"
_ACTIVATION_GATE = "book_intake_layer_frozen"
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")

_FROZEN_MODULES = (
    "core/book_intake/__init__.py",
    "core/book_intake/corruption_detector.py",
    "core/book_intake/decoder.py",
    "core/book_intake/encoding_detector.py",
    "core/book_intake/errors.py",
    "core/book_intake/intake_package.py",
    "core/book_intake/language_detector.py",
    "core/book_intake/manifest.py",
    "core/book_intake/models.py",
    "core/book_intake/preflight.py",
    "core/book_intake/source_reader.py",
)

_PUBLIC_API = (
    "AmbiguousEncodingError",
    "BinaryContentDetectedError",
    "BookIntakeProcessor",
    "BookIntakeResult",
    "BookIntakeManifest",
    "BookIntakeManifestBuilder",
    "BookPreflightAnalyzer",
    "BookPreflightResult",
    "BookManifestCorruption",
    "BookManifestEncoding",
    "BookManifestLanguage",
    "BookManifestPreflight",
    "BookManifestSource",
    "BookManifestValidationError",
    "BookManifestWorkload",
    "DecodeFailedError",
    "DecodedSource",
    "EmptyFileError",
    "EncodingDetectionResult",
    "EncodingDetector",
    "EncodingError",
    "EncodingNotDetectedError",
    "FileTooLargeError",
    "FileNotFoundError",
    "Finding",
    "NotAFileError",
    "PreflightFinding",
    "SourceFileError",
    "SourceFileReader",
    "LanguageDetectionResult",
    "SourceLanguageDetector",
    "SourceReadResult",
    "TextCorruptionDetector",
    "TextQualityReport",
    "UnsupportedEncodingError",
    "UnsupportedExtensionError",
    "decode_source",
    "detect_encoding",
    "BookIntakeFreezeMetadata",
    "BookIntakeFreezeValidationError",
    "get_book_intake_freeze_metadata",
    "validate_book_intake_freeze",
)

_INVARIANTS = (
    "offline_only",
    "deterministic",
    "immutable_results",
    "source_content_preserved",
    "no_translation",
    "no_provider_execution",
    "no_network_execution",
    "no_manifest_file_write",
    "no_source_file_write",
    "canonical_manifest_json",
    "stable_content_fingerprint",
    "stable_manifest_fingerprint",
    "absolute_path_not_serialized",
    "intake_preflight_consistency_fail_closed",
    "unknown_language_not_auto_blocked",
    "mixed_language_requires_manual_review",
    "corruption_blocking_has_priority",
    "preflight_status_action_mapping_frozen",
    "manifest_schema_1_0_frozen",
)

_MANIFEST_TOP_LEVEL_FIELDS = (
    "schema_name",
    "schema_version",
    "source",
    "encoding",
    "language",
    "corruption",
    "preflight",
    "workload",
    "status",
    "action",
    "content_fingerprint",
    "manifest_fingerprint",
)

_STATUS_ACTION = {
    "ready": "proceed",
    "ready_with_warnings": "proceed_with_warning",
    "manual_review_required": "manual_review",
    "blocked": "reject",
}

_MANIFEST_RELATIVE_PATH = Path("manifests/book_intake_stage28_freeze_manifest.json")


class BookIntakeFreezeValidationError(RuntimeError):
    """Raised when the frozen Book Intake baseline no longer validates."""


@dataclass(frozen=True)
class BookIntakeFreezeMetadata:
    component_name: str
    freeze_version: str
    schema_version: str
    activation_gate: str
    frozen_modules: tuple[str, ...]
    public_api: tuple[str, ...]
    invariants: tuple[str, ...]


_METADATA = BookIntakeFreezeMetadata(
    component_name=_COMPONENT_NAME,
    freeze_version=_FREEZE_VERSION,
    schema_version=_SCHEMA_VERSION,
    activation_gate=_ACTIVATION_GATE,
    frozen_modules=_FROZEN_MODULES,
    public_api=_PUBLIC_API,
    invariants=_INVARIANTS,
)


def get_book_intake_freeze_metadata() -> BookIntakeFreezeMetadata:
    """Return immutable deterministic metadata for the Stage 2.8 freeze."""
    return _METADATA


def validate_book_intake_freeze() -> None:
    """Fail closed when the Stage 2.8 source, API, or schema baseline drifts."""
    try:
        repository_root = Path(__file__).resolve().parents[2]
        manifest_path = repository_root / _MANIFEST_RELATIVE_PATH
        raw_manifest = manifest_path.read_bytes()
        if raw_manifest.startswith(b"\xef\xbb\xbf"):
            raise BookIntakeFreezeValidationError("Freeze manifest must not contain a BOM.")
        manifest_text = raw_manifest.decode("utf-8")
        manifest = json.loads(manifest_text)
        canonical = json.dumps(
            manifest,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        if manifest_text not in {canonical, canonical + "\n"}:
            raise BookIntakeFreezeValidationError("Freeze manifest is not canonical JSON.")

        _validate_manifest_contract(manifest)
        _validate_public_api()
        _validate_source_inventory(repository_root, manifest)
        _validate_schema_contract()
    except BookIntakeFreezeValidationError:
        raise
    except Exception as exc:
        raise BookIntakeFreezeValidationError(
            f"Book Intake freeze validation failed: {exc}"
        ) from exc


def _validate_manifest_contract(manifest: dict[str, Any]) -> None:
    expected_scalars = {
        "component": _COMPONENT_NAME,
        "stage": _FREEZE_VERSION,
        "freeze_version": _FREEZE_VERSION,
        "schema_name": _SCHEMA_NAME,
        "schema_version": _SCHEMA_VERSION,
        "activation_gate": _ACTIVATION_GATE,
        "provider_requests_added": 0,
        "network_requests_added": 0,
        "translation_executions_added": 0,
        "production_hooks_added": 0,
        "production_integration_authorized": False,
        "translation_runtime_integration_authorized": False,
        "provider_execution_authorized": False,
        "automatic_translation_authorized": False,
    }
    for key, expected in expected_scalars.items():
        if manifest.get(key) != expected:
            raise BookIntakeFreezeValidationError(f"Invalid freeze manifest field: {key}.")
    if tuple(manifest.get("public_api", ())) != _PUBLIC_API:
        raise BookIntakeFreezeValidationError("Frozen public API inventory drifted.")
    if tuple(manifest.get("invariants", ())) != _INVARIANTS:
        raise BookIntakeFreezeValidationError("Frozen invariant inventory drifted.")
    tests = manifest.get("validation_tests")
    if not isinstance(tests, list) or not tests or len(tests) != len(set(tests)):
        raise BookIntakeFreezeValidationError("Validation test inventory is invalid.")


def _validate_public_api() -> None:
    import core.book_intake as package

    exports = tuple(package.__all__)
    if exports != _PUBLIC_API:
        raise BookIntakeFreezeValidationError("core.book_intake.__all__ drifted.")
    if len(exports) != len(set(exports)):
        raise BookIntakeFreezeValidationError("Duplicate public API export detected.")
    for name in exports:
        if not name or name.startswith("_"):
            raise BookIntakeFreezeValidationError("Private or empty public API name detected.")
        value = getattr(package, name, None)
        if value is None:
            raise BookIntakeFreezeValidationError(f"Missing public API export: {name}.")
        module_name = getattr(value, "__module__", "")
        if module_name and not module_name.startswith("core.book_intake"):
            raise BookIntakeFreezeValidationError(
                f"Public API is outside Book Intake: {name}."
            )


def _validate_source_inventory(repository_root: Path, manifest: dict[str, Any]) -> None:
    entries = manifest.get("frozen_files")
    if not isinstance(entries, list):
        raise BookIntakeFreezeValidationError("Frozen file inventory is missing.")
    paths = [entry.get("path") for entry in entries if isinstance(entry, dict)]
    if len(paths) != len(entries) or len(paths) != len(set(paths)):
        raise BookIntakeFreezeValidationError("Duplicate or invalid frozen file path.")
    if paths != sorted(paths) or tuple(paths) != _FROZEN_MODULES:
        raise BookIntakeFreezeValidationError("Frozen file inventory is incomplete or unsorted.")

    package_dir = repository_root / "core" / "book_intake"
    discovered = tuple(
        sorted(
            path.relative_to(repository_root).as_posix()
            for path in package_dir.glob("*.py")
            if path.name != "freeze.py"
        )
    )
    if discovered != _FROZEN_MODULES:
        raise BookIntakeFreezeValidationError("Formal Book Intake source inventory drifted.")

    for entry in entries:
        relative = entry["path"]
        pure_path = PurePosixPath(relative)
        if (
            pure_path.is_absolute()
            or ".." in pure_path.parts
            or not relative.startswith("core/book_intake/")
            or not relative.endswith(".py")
        ):
            raise BookIntakeFreezeValidationError(f"Invalid frozen path: {relative}.")
        expected_hash = entry.get("sha256")
        if not isinstance(expected_hash, str) or not _HEX_64.fullmatch(expected_hash):
            raise BookIntakeFreezeValidationError(f"Invalid SHA-256 for: {relative}.")
        source_path = repository_root.joinpath(*pure_path.parts)
        if not source_path.is_file():
            raise BookIntakeFreezeValidationError(f"Frozen file is missing: {relative}.")
        observed_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if observed_hash != expected_hash:
            raise BookIntakeFreezeValidationError(f"Frozen file hash mismatch: {relative}.")


def _validate_schema_contract() -> None:
    from . import intake_package, manifest, preflight
    from .manifest import (
        BookIntakeManifest,
        BookManifestCorruption,
        BookManifestEncoding,
        BookManifestLanguage,
        BookManifestPreflight,
        BookManifestSource,
        BookManifestWorkload,
    )

    if manifest._SCHEMA_NAME != _SCHEMA_NAME or manifest._SCHEMA_VERSION != _SCHEMA_VERSION:
        raise BookIntakeFreezeValidationError("Book Intake manifest schema drifted.")
    if tuple(field.name for field in fields(BookIntakeManifest)) != _MANIFEST_TOP_LEVEL_FIELDS:
        raise BookIntakeFreezeValidationError("Manifest top-level fields drifted.")
    nested_models = (
        BookManifestSource,
        BookManifestEncoding,
        BookManifestLanguage,
        BookManifestCorruption,
        BookManifestPreflight,
        BookManifestWorkload,
    )
    if any(
        not is_dataclass(model) or not model.__dataclass_params__.frozen
        for model in nested_models
    ):
        raise BookIntakeFreezeValidationError("Manifest section immutability drifted.")
    if intake_package._STATUS_TO_ACTION != _STATUS_ACTION:
        raise BookIntakeFreezeValidationError("Intake status/action mapping drifted.")
    if manifest._STATUS_ACTION != _STATUS_ACTION:
        raise BookIntakeFreezeValidationError("Manifest status/action mapping drifted.")
    observed_preflight = {
        status: preflight._recommended_action(status) for status in _STATUS_ACTION
    }
    if observed_preflight != _STATUS_ACTION:
        raise BookIntakeFreezeValidationError("Preflight status/action mapping drifted.")
