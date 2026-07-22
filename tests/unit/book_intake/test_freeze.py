from __future__ import annotations

import hashlib
import inspect
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass
from pathlib import Path

import pytest

import core.book_intake as book_intake
import core.book_intake.freeze as freeze_module
import core.book_intake.intake_package as intake_module
import core.book_intake.manifest as manifest_module
from core.book_intake import (
    BookIntakeFreezeMetadata,
    BookIntakeFreezeValidationError,
    BookIntakeManifest,
    BookIntakeManifestBuilder,
    BookIntakeProcessor,
    BookPreflightAnalyzer,
    EncodingDetector,
    SourceFileReader,
    SourceLanguageDetector,
    TextCorruptionDetector,
    get_book_intake_freeze_metadata,
    validate_book_intake_freeze,
)
from core.book_intake.corruption_detector import TextQualityReport
from core.book_intake.models import BookIntakeResult, LanguageDetectionResult


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_FREEZE_MANIFEST = (
    _REPOSITORY_ROOT / "manifests" / "book_intake_stage28_freeze_manifest.json"
)


def _canonical_bytes(payload: dict[str, object]) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _intake(text: str, *, status: str = "ready") -> BookIntakeResult:
    language = SourceLanguageDetector().detect(text)
    quality = TextCorruptionDetector().analyze(text)
    action = {
        "ready": "proceed",
        "ready_with_warnings": "proceed_with_warning",
        "manual_review_required": "manual_review",
        "blocked": "reject",
    }[status]
    return BookIntakeResult(
        source_path=Path("fixture.txt"),
        file_name="fixture.txt",
        file_size_bytes=len(text.encode("utf-8")),
        encoding="utf-8",
        encoding_confidence="high",
        text=text,
        text_length=len(text),
        quality_report=quality,
        language_result=language,
        status=status,
        recommended_action=action,
        summary="fixture",
    )


def test_freeze_metadata_is_frozen_and_exact() -> None:
    metadata = get_book_intake_freeze_metadata()
    assert isinstance(metadata, BookIntakeFreezeMetadata)
    assert is_dataclass(metadata)
    assert metadata.__dataclass_params__.frozen
    assert metadata.component_name == "ntpe.book_intake"
    assert metadata.freeze_version == "2.8"
    assert metadata.schema_version == "1.0"
    assert metadata.activation_gate == "book_intake_layer_frozen"
    assert isinstance(metadata.frozen_modules, tuple)
    assert isinstance(metadata.public_api, tuple)
    assert isinstance(metadata.invariants, tuple)
    with pytest.raises(FrozenInstanceError):
        metadata.freeze_version = "changed"


def test_freeze_metadata_is_deterministic_and_environment_free() -> None:
    first = get_book_intake_freeze_metadata()
    assert first is get_book_intake_freeze_metadata()
    assert first == get_book_intake_freeze_metadata()
    serialized = repr(first).lower()
    forbidden = ("timestamp", "uuid", "hostname", "username", "git commit")
    assert not any(token in serialized for token in forbidden)
    assert not re.search(r"(?:[a-z]:[\\/]|/home/|/users/)", serialized)


def test_frozen_public_api_is_exact_unique_and_importable() -> None:
    metadata = get_book_intake_freeze_metadata()
    assert tuple(book_intake.__all__) == metadata.public_api
    assert len(metadata.public_api) == len(set(metadata.public_api)) == 42
    assert all(name and not name.startswith("_") for name in metadata.public_api)
    assert all(getattr(book_intake, name, None) is not None for name in metadata.public_api)


def test_stage_21_through_27_primary_api_remains_available() -> None:
    public_api = (
        SourceFileReader,
        EncodingDetector,
        TextCorruptionDetector,
        SourceLanguageDetector,
        BookIntakeProcessor,
        BookPreflightAnalyzer,
        BookIntakeManifestBuilder,
    )
    assert all(item.__module__.startswith("core.book_intake") for item in public_api)


def test_freeze_validation_succeeds_without_return_payload() -> None:
    assert validate_book_intake_freeze() is None


def test_freeze_manifest_is_canonical_deterministic_json() -> None:
    raw = _FREEZE_MANIFEST.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    payload = json.loads(raw.decode("utf-8"))
    assert raw == _canonical_bytes(payload)
    assert payload["schema_name"] == "ntpe.book_intake_manifest"
    assert payload["schema_version"] == "1.0"
    assert payload["activation_gate"] == "book_intake_layer_frozen"


def test_source_hash_inventory_is_complete_sorted_and_valid() -> None:
    payload = json.loads(_FREEZE_MANIFEST.read_text(encoding="utf-8"))
    entries = payload["frozen_files"]
    paths = [entry["path"] for entry in entries]
    assert tuple(paths) == get_book_intake_freeze_metadata().frozen_modules
    assert paths == sorted(paths)
    assert len(paths) == len(set(paths)) == 11
    for entry in entries:
        assert re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
        assert "\\" not in entry["path"]
        assert not PurePathChecks.is_absolute(entry["path"])
        observed = hashlib.sha256((_REPOSITORY_ROOT / entry["path"]).read_bytes()).hexdigest()
        assert observed == entry["sha256"]


class PurePathChecks:
    @staticmethod
    def is_absolute(value: str) -> bool:
        return value.startswith("/") or bool(re.match(r"^[A-Za-z]:", value))


def test_source_hash_change_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = Path.read_bytes

    def changed(path: Path) -> bytes:
        data = original(path)
        return data + b"drift" if path.name == "source_reader.py" else data

    monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(BookIntakeFreezeValidationError, match="hash mismatch"):
        validate_book_intake_freeze()


def test_missing_inventory_entry_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = Path.read_bytes
    payload = json.loads(_FREEZE_MANIFEST.read_text(encoding="utf-8"))
    payload["frozen_files"] = payload["frozen_files"][:-1]
    changed_manifest = _canonical_bytes(payload)

    def changed(path: Path) -> bytes:
        return changed_manifest if path.name == _FREEZE_MANIFEST.name else original(path)

    monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(BookIntakeFreezeValidationError, match="incomplete or unsorted"):
        validate_book_intake_freeze()


def test_public_api_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(book_intake, "__all__", [*book_intake.__all__, "UnexpectedHelper"])
    with pytest.raises(BookIntakeFreezeValidationError, match="__all__ drifted"):
        validate_book_intake_freeze()


def test_freeze_validation_reads_only_manifest_and_frozen_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = Path.read_bytes
    observed: list[Path] = []

    def recording(path: Path) -> bytes:
        observed.append(path.resolve())
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", recording)
    validate_book_intake_freeze()
    allowed = {
        (_REPOSITORY_ROOT / relative).resolve()
        for relative in get_book_intake_freeze_metadata().frozen_modules
    }
    allowed.add(_FREEZE_MANIFEST.resolve())
    assert set(observed) == allowed


def test_freeze_validation_performs_no_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("write attempted")

    monkeypatch.setattr(Path, "write_bytes", fail)
    monkeypatch.setattr(Path, "write_text", fail)
    assert validate_book_intake_freeze() is None


def test_schema_and_nested_immutability_contract_is_frozen() -> None:
    assert manifest_module._SCHEMA_NAME == "ntpe.book_intake_manifest"
    assert manifest_module._SCHEMA_VERSION == "1.0"
    assert tuple(field.name for field in fields(BookIntakeManifest)) == (
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
    nested = (
        book_intake.BookManifestSource,
        book_intake.BookManifestEncoding,
        book_intake.BookManifestLanguage,
        book_intake.BookManifestCorruption,
        book_intake.BookManifestPreflight,
        book_intake.BookManifestWorkload,
    )
    assert all(model.__dataclass_params__.frozen for model in nested)


def test_status_action_contract_is_frozen() -> None:
    expected = {
        "ready": "proceed",
        "ready_with_warnings": "proceed_with_warning",
        "manual_review_required": "manual_review",
        "blocked": "reject",
    }
    assert intake_module._STATUS_TO_ACTION == expected
    assert manifest_module._STATUS_ACTION == expected


def test_finding_policy_codes_and_order_are_frozen() -> None:
    source = inspect.getsource(book_intake.preflight._build_findings)
    expected_codes = (
        "EMPTY_CONTENT",
        "VERY_SHORT_BOOK",
        "LARGE_BOOK",
        "VERY_LARGE_BOOK",
        "EXTREME_BOOK_SIZE",
        "EXCESSIVE_LINE_LENGTH",
        "SINGLE_LINE_BOOK",
        "LOW_PARAGRAPH_STRUCTURE",
        "HIGH_BLANK_LINE_RATIO",
        "HIGH_CHUNK_WORKLOAD",
        "EXTREME_CHUNK_WORKLOAD",
        "INTAKE_BLOCKED",
        "INTAKE_MANUAL_REVIEW",
        "INTAKE_WARNING",
    )
    observed_codes = tuple(
        code for code in expected_codes if f'"{code}"' in source
    )
    assert observed_codes == expected_codes


def test_corruption_blocking_has_priority() -> None:
    text = ("\x00\x01\ufffd" * 20) + "한국어"
    quality = TextCorruptionDetector().analyze(text)
    intake = _intake(text, status="blocked")
    intake = BookIntakeResult(
        **{**intake.__dict__, "quality_report": quality}
    )
    result = BookPreflightAnalyzer().analyze(intake)
    assert result.status == "blocked"
    assert result.recommended_action == "reject"
    assert result.risk_findings[-1].code == "INTAKE_BLOCKED"


def test_preflight_finding_order_repeats_exactly() -> None:
    intake = _intake("가" * 20_001, status="blocked")
    analyzer = BookPreflightAnalyzer(source_chunk_size=1)
    results = tuple(analyzer.analyze(intake) for _ in range(3))
    expected = (
        "EXCESSIVE_LINE_LENGTH",
        "SINGLE_LINE_BOOK",
        "LOW_PARAGRAPH_STRUCTURE",
        "EXTREME_CHUNK_WORKLOAD",
        "INTAKE_BLOCKED",
    )
    assert all(tuple(f.code for f in result.risk_findings) == expected for result in results)
    assert results[0] == results[1] == results[2]


def test_freeze_module_has_no_provider_network_or_translation_execution() -> None:
    source = inspect.getsource(freeze_module).lower()
    forbidden_imports = ("import requests", "from requests", "import urllib", "import socket")
    assert not any(token in source for token in forbidden_imports)
    assert "provider.invoke(" not in source
    assert "translation_runtime.invoke(" not in source
    assert "translate(" not in source
