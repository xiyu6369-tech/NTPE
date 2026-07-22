from __future__ import annotations

import hashlib
import inspect
import json
import re
from dataclasses import FrozenInstanceError, is_dataclass, replace
from pathlib import Path

import pytest

from core.book_intake import (
    BookIntakeManifest,
    BookIntakeManifestBuilder,
    BookManifestCorruption,
    BookManifestEncoding,
    BookManifestLanguage,
    BookManifestPreflight,
    BookManifestSource,
    BookManifestValidationError,
    BookManifestWorkload,
)
from core.book_intake.corruption_detector import Finding, TextQualityReport
from core.book_intake.models import (
    BookIntakeResult,
    BookPreflightResult,
    LanguageDetectionResult,
    PreflightFinding,
)
import core.book_intake.manifest as manifest_module


def _pair(
    text: str = "這是一段穩定的中文內容。\n\n第二段內容。",
    *,
    file_name: str = "小說.txt",
    source_path: Path | None = None,
    intake_findings: tuple[Finding, ...] = (),
    preflight_findings: tuple[PreflightFinding, ...] = (),
    status: str = "ready",
    action: str = "proceed",
) -> tuple[BookIntakeResult, BookPreflightResult]:
    path = source_path or Path(file_name)
    quality_status = "warning" if intake_findings else "clean"
    quality = TextQualityReport(quality_status, intake_findings, 90, "accept", "summary")
    language = LanguageDetectionResult("zh", 95, (("cjk", 10),), "zh-Hant-zh-Hans", "Chinese")
    intake = BookIntakeResult(
        source_path=path,
        file_name=file_name,
        file_size_bytes=len(text.encode("utf-8")),
        encoding="utf-8",
        encoding_confidence="high",
        text=text,
        text_length=len(text),
        quality_report=quality,
        language_result=language,
        status="ready_with_warnings" if intake_findings else "ready",
        recommended_action="proceed_with_warning" if intake_findings else "proceed",
        summary="intake",
    )
    lines = text.splitlines() if text else []
    non_empty_lines = sum(bool(line.strip()) for line in lines)
    preflight = BookPreflightResult(
        source_path=path,
        file_name=file_name,
        source_language="zh",
        encoding="utf-8",
        character_count=len(text),
        non_whitespace_character_count=sum(not char.isspace() for char in text),
        line_count=len(lines),
        non_empty_line_count=non_empty_lines,
        paragraph_count=2 if text else 0,
        estimated_word_count=sum(not char.isspace() for char in text),
        estimated_chunk_count=1 if text else 0,
        estimated_source_tokens=(len(text) + 1) // 2,
        largest_line_length=max((len(line) for line in lines), default=0),
        average_line_length=(
            round(sum(len(line) for line in lines) / len(lines), 2) if lines else 0.0
        ),
        risk_findings=preflight_findings,
        status=status,
        recommended_action=action,
        summary="預檢完成。",
        source_chunk_size=600,
        estimated_chars_per_token=2.0,
    )
    return intake, preflight


def _build(**kwargs: object) -> BookIntakeManifest:
    intake, preflight = _pair(**kwargs)
    return BookIntakeManifestBuilder().build(intake, preflight)


def test_manifest_and_nested_models_are_frozen_dataclasses() -> None:
    manifest = _build()
    values = (
        manifest,
        manifest.source,
        manifest.encoding,
        manifest.language,
        manifest.corruption,
        manifest.preflight,
        manifest.workload,
    )
    assert all(is_dataclass(value) for value in values)
    with pytest.raises(FrozenInstanceError):
        manifest.status = "blocked"
    with pytest.raises(FrozenInstanceError):
        manifest.source.source_name = "other.txt"


def test_findings_are_immutable_tuples() -> None:
    finding = PreflightFinding("ONE", "warning", "one", 1, 2)
    manifest = _build(preflight_findings=(finding,))
    assert manifest.preflight.finding_codes == ("ONE",)
    assert manifest.preflight.finding_severities == ("warning",)
    with pytest.raises(TypeError):
        manifest.preflight.finding_codes[0] = "TWO"


def test_valid_builder_and_schema() -> None:
    manifest = _build()
    assert manifest.schema_name == "ntpe.book_intake_manifest"
    assert manifest.schema_version == "1.0"
    assert manifest.status == "ready"
    assert manifest.action == "proceed"


def test_source_mapping_is_path_safe() -> None:
    manifest = _build(file_name=r"D:\Books\小說.txt", source_path=Path(r"D:\Books\小說.txt"))
    assert manifest.source == BookManifestSource("小說.txt", ".txt", 56, "text")
    assert "D:\\Books" not in manifest.to_json()


def test_encoding_mapping_does_not_invent_confidence_or_bom() -> None:
    encoding = _build().encoding
    assert encoding == BookManifestEncoding("utf-8", None, None, "decoded")


def test_language_mapping_normalizes_existing_percentage() -> None:
    language = _build().language
    assert language == BookManifestLanguage("zh", 0.95, "zh-Hant-zh-Hans")


def test_corruption_mapping_counts_and_order() -> None:
    findings = (
        Finding("replacement_character", "warning", 2, "hidden"),
        Finding("control_character", "warning", 3, "hidden"),
        Finding("null_character", "error", 1, "hidden"),
    )
    corruption = _build(intake_findings=findings).corruption
    assert corruption == BookManifestCorruption(
        "warning", 2, 1, 3,
        ("replacement_character", "control_character", "null_character"),
    )
    assert "hidden" not in _build(intake_findings=findings).to_json()


def test_preflight_mapping_preserves_aligned_findings() -> None:
    findings = (
        PreflightFinding("FIRST", "info", "ignored", 1, 1),
        PreflightFinding("SECOND", "warning", "ignored", 2, 2),
    )
    preflight = _build(
        preflight_findings=findings,
        status="ready_with_warnings",
        action="proceed_with_warning",
    ).preflight
    assert preflight == BookManifestPreflight(
        "ready_with_warnings",
        "proceed_with_warning",
        "預檢完成。",
        ("FIRST", "SECOND"),
        ("info", "warning"),
    )


def test_workload_mapping_is_direct() -> None:
    workload = _build().workload
    assert workload.character_count == 20
    assert workload.line_count == 3
    assert workload.blank_line_count == 1
    assert workload.paragraph_count == 2
    assert workload.estimated_chunk_count == 1
    assert workload.source_chunk_size == 600
    assert workload.chars_per_token == 2.0


def test_status_and_action_are_inherited() -> None:
    manifest = _build(status="blocked", action="reject")
    assert manifest.status == manifest.preflight.status == "blocked"
    assert manifest.action == manifest.preflight.action == "reject"


@pytest.mark.parametrize("text", ["內容", "", "內容\n", " 內容 "])
def test_content_fingerprint_matches_exact_utf8_text(text: str) -> None:
    manifest = _build(text=text, status="blocked" if not text else "ready", action="reject" if not text else "proceed")
    assert manifest.content_fingerprint == hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_newline_and_outer_whitespace_change_content_fingerprint() -> None:
    fingerprints = {
        _build(text="內容").content_fingerprint,
        _build(text="內容\n").content_fingerprint,
        _build(text=" 內容 ").content_fingerprint,
    }
    assert len(fingerprints) == 3


def test_manifest_fingerprint_is_deterministic() -> None:
    assert _build().manifest_fingerprint == _build().manifest_fingerprint


def test_workload_difference_changes_manifest_fingerprint() -> None:
    intake, preflight = _pair()
    first = BookIntakeManifestBuilder().build(intake, preflight)
    second = BookIntakeManifestBuilder().build(
        intake, replace(preflight, estimated_chunk_count=2)
    )
    assert first.manifest_fingerprint != second.manifest_fingerprint


def test_finding_difference_changes_manifest_fingerprint() -> None:
    first = _build()
    finding = PreflightFinding("NEW", "info", "ignored", 1, 1)
    second = _build(preflight_findings=(finding,))
    assert first.manifest_fingerprint != second.manifest_fingerprint


def test_manifest_fingerprint_excludes_itself() -> None:
    manifest = _build()
    payload = manifest.to_dict()
    observed = payload.pop("manifest_fingerprint")
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert observed == hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_fingerprints_are_lowercase_sha256() -> None:
    manifest = _build()
    assert re.fullmatch(r"[0-9a-f]{64}", manifest.content_fingerprint)
    assert re.fullmatch(r"[0-9a-f]{64}", manifest.manifest_fingerprint)


def test_canonical_json_is_deterministic_compact_and_unicode() -> None:
    first = _build().to_json()
    second = _build().to_json()
    assert first == second
    assert "小說.txt" in first
    assert "\\u5c0f" not in first
    assert ": " not in first
    assert ", " not in first
    assert json.loads(first)["schema_name"] == "ntpe.book_intake_manifest"


def test_canonical_json_keys_are_sorted() -> None:
    payload = _build().to_dict()
    expected = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert _build().to_json() == expected


def test_to_dict_is_detached_and_tuples_become_json_arrays() -> None:
    finding = PreflightFinding("ONE", "warning", "ignored", 1, 2)
    manifest = _build(preflight_findings=(finding,))
    payload = manifest.to_dict()
    payload["source"]["source_name"] = "changed.txt"
    assert manifest.source.source_name == "小說.txt"
    assert json.loads(manifest.to_json())["preflight"]["finding_codes"] == ["ONE"]


@pytest.mark.parametrize(
    ("field", "value"),
    [("schema_name", "wrong"), ("schema_version", "2.0"), ("content_fingerprint", "bad"), ("manifest_fingerprint", "A" * 64)],
)
def test_invalid_top_level_fields_are_rejected(field: str, value: str) -> None:
    with pytest.raises(BookManifestValidationError):
        replace(_build(), **{field: value})


@pytest.mark.parametrize(
    ("field", "value"),
    [("character_count", -1), ("line_count", -1), ("estimated_chunk_count", -1), ("estimated_token_count", -1)],
)
def test_negative_workload_values_are_rejected(field: str, value: int) -> None:
    manifest = _build()
    with pytest.raises(BookManifestValidationError):
        replace(manifest, workload=replace(manifest.workload, **{field: value}))


@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_invalid_language_confidence_is_rejected(value: float) -> None:
    manifest = _build()
    with pytest.raises(BookManifestValidationError):
        replace(manifest, language=replace(manifest.language, language_confidence=value))


def test_invalid_encoding_confidence_is_rejected() -> None:
    manifest = _build()
    with pytest.raises(BookManifestValidationError):
        replace(manifest, encoding=replace(manifest.encoding, confidence=1.1))


@pytest.mark.parametrize(
    ("status", "action"),
    [("invalid", "proceed"), ("ready", "invalid"), ("ready", "reject")],
)
def test_invalid_status_action_values_are_rejected(status: str, action: str) -> None:
    with pytest.raises(BookManifestValidationError):
        replace(_build(), status=status, action=action)


def test_empty_finding_code_is_rejected() -> None:
    manifest = _build()
    invalid = replace(manifest.preflight, finding_codes=("",), finding_severities=("warning",))
    with pytest.raises(BookManifestValidationError):
        replace(manifest, preflight=invalid)


def test_finding_code_severity_length_mismatch_is_rejected() -> None:
    manifest = _build()
    invalid = replace(manifest.preflight, finding_codes=("ONE",), finding_severities=())
    with pytest.raises(BookManifestValidationError):
        replace(manifest, preflight=invalid)


@pytest.mark.parametrize(
    ("field", "value"),
    [("source_chunk_size", 0), ("chars_per_token", 0.0)],
)
def test_invalid_workload_configuration_is_rejected(field: str, value: float) -> None:
    manifest = _build()
    with pytest.raises(BookManifestValidationError):
        replace(manifest, workload=replace(manifest.workload, **{field: value}))


def test_input_types_are_validated() -> None:
    builder = BookIntakeManifestBuilder()
    intake, preflight = _pair()
    with pytest.raises(TypeError):
        builder.build(object(), preflight)
    with pytest.raises(TypeError):
        builder.build(intake, object())


@pytest.mark.parametrize(
    "field", ["file_name", "source_path", "encoding", "language", "character_count"]
)
def test_source_mismatch_fails_closed(field: str) -> None:
    intake, preflight = _pair()
    if field == "file_name":
        preflight = replace(preflight, file_name="other.txt")
    elif field == "source_path":
        preflight = replace(preflight, source_path=Path("other.txt"))
    elif field == "encoding":
        preflight = replace(preflight, encoding="cp949")
    elif field == "language":
        preflight = replace(preflight, source_language="ko")
    else:
        preflight = replace(preflight, character_count=preflight.character_count + 1)
    with pytest.raises(BookManifestValidationError):
        BookIntakeManifestBuilder().build(intake, preflight)


@pytest.mark.parametrize(
    "source_name",
    [r"C:\Users\reader\book.txt", "/home/reader/book.txt"],
)
def test_absolute_paths_are_reduced_to_basename(source_name: str) -> None:
    manifest = _build(file_name=source_name, source_path=Path(source_name))
    assert manifest.source.source_name == "book.txt"
    assert "Users" not in manifest.to_json()
    assert "/home/" not in manifest.to_json()


def test_manifest_rejects_nested_absolute_path() -> None:
    manifest = _build()
    with pytest.raises(BookManifestValidationError):
        replace(manifest, preflight=replace(manifest.preflight, summary=r"C:\secret\book.txt"))


def test_builder_performs_no_file_reads_or_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("file access attempted")

    monkeypatch.setattr(Path, "read_text", fail)
    monkeypatch.setattr(Path, "read_bytes", fail)
    monkeypatch.setattr(Path, "write_text", fail)
    monkeypatch.setattr(Path, "write_bytes", fail)
    assert _build().status == "ready"


def test_module_has_no_network_provider_or_translation_dependency() -> None:
    source = inspect.getsource(manifest_module).lower()
    assert "requests" not in source
    assert "urllib" not in source
    assert "provider" not in source
    assert "translation" not in source


def test_builder_does_not_call_existing_detectors_or_analyzers(monkeypatch: pytest.MonkeyPatch) -> None:
    from core.book_intake.corruption_detector import TextCorruptionDetector
    from core.book_intake.language_detector import SourceLanguageDetector
    from core.book_intake.preflight import BookPreflightAnalyzer

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("analysis rerun attempted")

    monkeypatch.setattr(TextCorruptionDetector, "analyze", fail)
    monkeypatch.setattr(SourceLanguageDetector, "detect", fail)
    monkeypatch.setattr(BookPreflightAnalyzer, "analyze", fail)
    assert _build().status == "ready"


def test_existing_finding_order_is_preserved() -> None:
    findings = tuple(
        PreflightFinding(code, "warning", "ignored", index, 1)
        for index, code in enumerate(("THIRD", "FIRST", "SECOND"))
    )
    manifest = _build(
        preflight_findings=findings,
        status="ready_with_warnings",
        action="proceed_with_warning",
    )
    assert manifest.preflight.finding_codes == ("THIRD", "FIRST", "SECOND")
