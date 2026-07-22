from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.book_intake import (
    BookIntakeManifestBuilder,
    BookIntakeProcessor,
    BookPreflightAnalyzer,
    EncodingDetector,
    SourceLanguageDetector,
    TextCorruptionDetector,
    decode_source,
    validate_book_intake_freeze,
)
from core.book_intake.models import BookIntakeResult


def _snapshot(source_path: Path) -> tuple[object, ...]:
    raw_bytes = source_path.read_bytes()
    encoding = EncodingDetector().detect(raw_bytes)
    decoded = decode_source(raw_bytes, encoding)
    intake = BookIntakeProcessor().process(source_path)
    preflight = BookPreflightAnalyzer().analyze(intake)
    manifest = BookIntakeManifestBuilder().build(intake, preflight)
    return (
        encoding,
        decoded,
        intake.quality_report,
        intake.language_result,
        intake.status,
        intake.recommended_action,
        intake.summary,
        preflight,
        manifest.to_dict(),
        manifest.to_json(),
        manifest.content_fingerprint,
        manifest.manifest_fingerprint,
    )


@pytest.mark.parametrize(
    ("name", "text", "expected_language"),
    [
        ("korean.txt", "한국어 장편 문장입니다. " * 100, "ko"),
        ("traditional_chinese.txt", "這是穩定的繁體中文長篇內容。" * 100, "zh"),
        ("japanese.txt", "これは安定した日本語の文章です。" * 100, "ja"),
        ("english.txt", "This is stable English long-form book content. " * 100, "en"),
        ("mixed.txt", "한국어문장English" * 100, "mixed"),
        ("unknown.txt", "1234567890 !? 1234567890 !?" * 100, "unknown"),
    ],
)
def test_full_pipeline_is_deterministic_three_times(
    tmp_path: Path,
    name: str,
    text: str,
    expected_language: str,
) -> None:
    source_path = tmp_path / name
    source_path.write_text(text, encoding="utf-8", newline="")
    snapshots = tuple(_snapshot(source_path) for _ in range(3))
    assert snapshots[0] == snapshots[1] == snapshots[2]
    assert snapshots[0][3].language == expected_language
    manifest_payload = snapshots[0][8]
    assert manifest_payload["schema_name"] == "ntpe.book_intake_manifest"
    assert manifest_payload["schema_version"] == "1.0"
    assert snapshots[0][9].encode("utf-8") == snapshots[1][9].encode("utf-8")


def test_unknown_language_is_manual_review_not_blocked(tmp_path: Path) -> None:
    source_path = tmp_path / "unknown.txt"
    source_path.write_text("1234567890 !? " * 100, encoding="utf-8")
    intake = BookIntakeProcessor().process(source_path)
    assert intake.language_result.language == "unknown"
    assert intake.status == "manual_review_required"
    assert intake.recommended_action == "manual_review"


def test_mixed_language_requires_manual_review(tmp_path: Path) -> None:
    source_path = tmp_path / "mixed.txt"
    source_path.write_text("한국어문장English" * 100, encoding="utf-8")
    intake = BookIntakeProcessor().process(source_path)
    assert intake.language_result.language == "mixed"
    assert intake.status == "manual_review_required"
    assert intake.recommended_action == "manual_review"


def _synthetic_intake(text: str, *, status: str) -> BookIntakeResult:
    language = SourceLanguageDetector().detect(text)
    quality = TextCorruptionDetector().analyze(text)
    action = {
        "ready": "proceed",
        "ready_with_warnings": "proceed_with_warning",
        "manual_review_required": "manual_review",
        "blocked": "reject",
    }[status]
    return BookIntakeResult(
        source_path=Path("synthetic.txt"),
        file_name="synthetic.txt",
        file_size_bytes=len(text.encode("utf-8")),
        encoding="utf-8",
        encoding_confidence="high",
        text=text,
        text_length=len(text),
        quality_report=quality,
        language_result=language,
        status=status,
        recommended_action=action,
        summary="synthetic",
    )


def test_empty_analyzer_and_manifest_path_is_deterministic() -> None:
    intake = _synthetic_intake("", status="manual_review_required")
    snapshots = []
    for _ in range(3):
        preflight = BookPreflightAnalyzer().analyze(intake)
        manifest = BookIntakeManifestBuilder().build(intake, preflight)
        snapshots.append((preflight, manifest.to_dict(), manifest.to_json()))
    assert snapshots[0] == snapshots[1] == snapshots[2]
    assert snapshots[0][0].status == "blocked"
    assert snapshots[0][0].recommended_action == "reject"
    assert snapshots[0][0].risk_findings[0].code == "EMPTY_CONTENT"


@pytest.mark.parametrize(
    ("text", "chunk_size", "expected_codes"),
    [
        ("short", 600, ("VERY_SHORT_BOOK",)),
        ("가" * 20_001, 600, (
            "EXCESSIVE_LINE_LENGTH",
            "SINGLE_LINE_BOOK",
            "LOW_PARAGRAPH_STRUCTURE",
        )),
        ("content\n" + "\n" * 99, 600, (
            "VERY_SHORT_BOOK",
            "HIGH_BLANK_LINE_RATIO",
        )),
        ("가" * 20_001, 1, (
            "EXCESSIVE_LINE_LENGTH",
            "SINGLE_LINE_BOOK",
            "LOW_PARAGRAPH_STRUCTURE",
            "EXTREME_CHUNK_WORKLOAD",
        )),
    ],
    ids=("very_short", "long_single_line", "high_blank_ratio", "large_workload"),
)
def test_preflight_policy_fixtures_repeat_deterministically(
    text: str,
    chunk_size: int,
    expected_codes: tuple[str, ...],
) -> None:
    intake = _synthetic_intake(text, status="ready")
    analyzer = BookPreflightAnalyzer(source_chunk_size=chunk_size)
    results = tuple(analyzer.analyze(intake) for _ in range(3))
    assert results[0] == results[1] == results[2]
    assert tuple(finding.code for finding in results[0].risk_findings) == expected_codes


def test_manifest_fingerprint_includes_content_and_excludes_itself(tmp_path: Path) -> None:
    source_path = tmp_path / "fingerprint.txt"
    source_path.write_text("固定內容。" * 100, encoding="utf-8")
    intake = BookIntakeProcessor().process(source_path)
    preflight = BookPreflightAnalyzer().analyze(intake)
    manifest = BookIntakeManifestBuilder().build(intake, preflight)
    payload = manifest.to_dict()
    observed = payload.pop("manifest_fingerprint")
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    import hashlib

    assert payload["content_fingerprint"] == manifest.content_fingerprint
    assert observed == hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_freeze_activation_and_boundary_manifest() -> None:
    assert validate_book_intake_freeze() is None
    root = Path(__file__).resolve().parents[2]
    payload = json.loads(
        (root / "manifests" / "book_intake_stage28_freeze_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["activation_gate"] == "book_intake_layer_frozen"
    assert payload["provider_requests_added"] == 0
    assert payload["network_requests_added"] == 0
    assert payload["translation_executions_added"] == 0
    assert payload["production_hooks_added"] == 0
    assert payload["production_integration_authorized"] is False
    assert payload["translation_runtime_integration_authorized"] is False
