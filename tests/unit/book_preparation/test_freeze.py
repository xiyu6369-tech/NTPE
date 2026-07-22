from __future__ import annotations

import hashlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass
from pathlib import Path

import pytest

import core.book_chunking as book_chunking
import core.book_preparation as book_preparation
import core.book_segmentation as book_segmentation
from core.book_chunking import BookChunkPlanner
from core.book_chunking.policy import DEFAULT_POLICY as CHUNK_POLICY
from core.book_preparation import (
    BookPreparationFinding,
    BookPreparationFreezeMetadata,
    BookPreparationFreezeValidationError,
    BookPreparationFreezeValidationResult,
    BookPreparationResult,
    get_book_preparation_freeze_metadata,
    validate_book_preparation_freeze,
)
from core.book_preparation import processor as preparation_processor
from core.book_segmentation import BookStructureSegmenter


_ROOT = Path(__file__).resolve().parents[3]
_MANIFEST = _ROOT / "manifests" / "book_preparation_stage34_freeze_manifest.json"


def _canonical_bytes(payload: dict[str, object]) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def test_freeze_metadata_and_validation_result_are_frozen_and_exact() -> None:
    metadata = get_book_preparation_freeze_metadata()
    assert isinstance(metadata, BookPreparationFreezeMetadata)
    assert is_dataclass(metadata) and metadata.__dataclass_params__.frozen
    assert metadata.component_name == "ntpe.book_preparation_pipeline"
    assert metadata.freeze_version == "3.4"
    assert metadata.schema_name == "ntpe.book_preparation"
    assert metadata.schema_version == "1.0"
    assert metadata.strategy == "deterministic_offline_book_preparation_v1"
    assert metadata.activation_gate == "book_preparation_pipeline_frozen"
    assert isinstance(metadata.frozen_modules, tuple)
    assert isinstance(metadata.public_api, tuple)
    assert isinstance(metadata.invariants, tuple)
    assert not any(
        (
            metadata.production_integration_authorized,
            metadata.translation_runtime_integration_authorized,
            metadata.provider_execution_authorized,
            metadata.automatic_translation_authorized,
        )
    )
    with pytest.raises(FrozenInstanceError):
        metadata.freeze_version = "changed"

    result = validate_book_preparation_freeze()
    assert isinstance(result, BookPreparationFreezeValidationResult)
    assert result.valid and result.hash_drift_count == 0
    assert result.checked_source_count == 15
    with pytest.raises(FrozenInstanceError):
        result.valid = False


def test_metadata_is_singleton_deterministic_and_environment_free() -> None:
    metadata = get_book_preparation_freeze_metadata()
    assert metadata is get_book_preparation_freeze_metadata()
    assert metadata == get_book_preparation_freeze_metadata()
    serialized = repr(metadata).lower()
    forbidden = ("timestamp", "uuid", "hostname", "username", "git commit")
    assert not any(token in serialized for token in forbidden)
    assert not re.search(r"(?:[a-z]:[\\/]|/home/|/users/)", serialized)


def test_frozen_public_api_is_exact_unique_importable_and_owned() -> None:
    metadata = get_book_preparation_freeze_metadata()
    packages = (
        (book_segmentation, "core.book_segmentation"),
        (book_chunking, "core.book_chunking"),
        (book_preparation, "core.book_preparation"),
    )
    observed = tuple(name for package, _ in packages for name in package.__all__)
    assert observed == metadata.public_api
    assert len(observed) == len(set(observed)) == 31
    for package, prefix in packages:
        for name in package.__all__:
            assert name and not name.startswith("_")
            value = getattr(package, name, None)
            assert value is not None
            assert value.__module__.startswith(prefix)


def test_manifest_is_canonical_bom_free_and_environment_free() -> None:
    raw = _MANIFEST.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    payload = json.loads(raw.decode("utf-8"))
    assert raw == _canonical_bytes(payload)
    assert payload["activation_gate"] == "book_preparation_pipeline_frozen"
    serialized = raw.decode("utf-8").lower()
    assert not any(token in serialized for token in ("timestamp", "uuid", "hostname", "username"))
    assert not re.search(r"(?:[a-z]:[\\/]|/home/|/users/)", serialized)


def test_source_inventory_is_complete_sorted_scoped_and_hashed() -> None:
    metadata = get_book_preparation_freeze_metadata()
    payload = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    entries = payload["frozen_files"]
    paths = [entry["path"] for entry in entries]
    assert tuple(paths) == metadata.frozen_modules
    assert paths == sorted(paths)
    assert len(paths) == len(set(paths)) == 15
    assert sum(path.startswith("core/book_segmentation/") for path in paths) == 5
    assert sum(path.startswith("core/book_chunking/") for path in paths) == 5
    assert sum(path.startswith("core/book_preparation/") for path in paths) == 5
    assert all("tests/" not in path and "artifacts/" not in path for path in paths)
    for entry in entries:
        assert "\\" not in entry["path"] and not Path(entry["path"]).is_absolute()
        assert re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
        assert hashlib.sha256((_ROOT / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]


def test_source_hash_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = Path.read_bytes

    def changed(path: Path) -> bytes:
        data = original(path)
        return data + b"drift" if path.name == "planner.py" else data

    monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(BookPreparationFreezeValidationError, match="hash mismatch"):
        validate_book_preparation_freeze()


@pytest.mark.parametrize("mutation", ["missing", "extra", "invalid_hash"])
def test_invalid_source_inventory_fails_closed(
    monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    original = Path.read_bytes
    payload = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    if mutation == "missing":
        payload["frozen_files"] = payload["frozen_files"][:-1]
    elif mutation == "extra":
        payload["frozen_files"].append(
            {"path": "core/book_preparation/unexpected.py", "sha256": "0" * 64}
        )
    else:
        payload["frozen_files"][0]["sha256"] = "INVALID"
    changed_manifest = _canonical_bytes(payload)

    def changed(path: Path) -> bytes:
        return changed_manifest if path.name == _MANIFEST.name else original(path)

    monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(BookPreparationFreezeValidationError):
        validate_book_preparation_freeze()


def test_public_api_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        book_preparation,
        "__all__",
        [*book_preparation.__all__, "UnexpectedPrivateHelper"],
    )
    with pytest.raises(BookPreparationFreezeValidationError, match="Public API"):
        validate_book_preparation_freeze()


def test_validation_reads_only_manifest_and_frozen_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = Path.read_bytes
    observed: list[Path] = []

    def recording(path: Path) -> bytes:
        observed.append(path.resolve())
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", recording)
    validate_book_preparation_freeze()
    allowed = {(_ROOT / relative).resolve() for relative in get_book_preparation_freeze_metadata().frozen_modules}
    allowed.add(_MANIFEST.resolve())
    assert set(observed) == allowed


def test_validation_performs_no_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("write attempted")

    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    assert validate_book_preparation_freeze().valid


def test_preparation_schema_models_and_status_contract_are_frozen() -> None:
    metadata = get_book_preparation_freeze_metadata()
    expected_fields = (
        "schema_name", "schema_version", "strategy", "source_name",
        "intake_result", "preflight_result", "intake_manifest",
        "segmentation_result", "chunk_plan", "source_content_fingerprint",
        "manifest_fingerprint", "segmentation_fingerprint",
        "chunk_plan_fingerprint", "status", "action", "findings", "summary",
        "preparation_fingerprint",
    )
    assert tuple(field.name for field in fields(BookPreparationResult)) == expected_fields
    assert BookPreparationResult.__dataclass_params__.frozen
    assert BookPreparationFinding.__dataclass_params__.frozen
    assert preparation_processor.SCHEMA_NAME == metadata.schema_name
    assert preparation_processor.SCHEMA_VERSION == metadata.schema_version
    assert preparation_processor.STRATEGY == metadata.strategy
    assert dict(preparation_processor._STATUS_ACTION) == {
        "ready": "proceed",
        "ready_with_warnings": "proceed_with_warning",
        "manual_review": "manual_review",
        "blocked": "reject",
    }


def test_chunk_defaults_and_boundary_priority_are_frozen() -> None:
    assert (
        CHUNK_POLICY.minimum_chunk_size,
        CHUNK_POLICY.target_chunk_size,
        CHUNK_POLICY.maximum_chunk_size,
    ) == (800, 2000, 2600)
    assert CHUNK_POLICY.boundary_priority == (
        "paragraph", "sentence", "line", "hard_limit"
    )


@pytest.mark.parametrize(
    "text",
    [
        "제1장\n내용입니다.\n제2장\n다음 내용입니다.",
        "第一章\n內容。\n第二章\n結尾。",
        "第一章\nこれは本文です。\n第二章\n終わり。",
        "Chapter 1\nText.\nChapter 2\nMore.",
        "序文\n\nChapter 1\r\nText.\r\nChapter 2\r\nMore.\r\n",
        "Chapter 1\n" + "x" * 3000,
        "Chapter 1\nA\nChapter 2\nB\nChapter 3\nC",
    ],
)
def test_segmentation_and_chunk_contracts_repeat_exactly(text: str) -> None:
    segmentations = tuple(
        BookStructureSegmenter().segment_text(text, source_name="fixture.txt")
        for _ in range(3)
    )
    assert segmentations[0] == segmentations[1] == segmentations[2]
    segmentation = segmentations[0]
    assert segmentation.reconstruct_text() == text
    if text:
        assert segmentation.sections[0].character_start == 0
        assert segmentation.sections[-1].character_end == len(text)
    plans = tuple(BookChunkPlanner().plan(segmentation) for _ in range(3))
    assert plans[0] == plans[1] == plans[2]
    assert plans[0].reconstruct_text() == text
    assert all(chunk.character_count <= plans[0].maximum_chunk_size for chunk in plans[0].chunks)
    for left, right in zip(plans[0].chunks, plans[0].chunks[1:]):
        assert left.source_character_end == right.source_character_start


def test_front_matter_no_heading_numeric_and_empty_contracts_are_frozen() -> None:
    front = BookStructureSegmenter().segment_text(
        "Title\n\nChapter 1\nText", source_name="fixture.txt"
    )
    assert front.sections[0].section_type == "front_matter"
    no_heading = BookStructureSegmenter().segment_text(
        "plain body text", source_name="fixture.txt"
    )
    assert no_heading.status == "manual_review"
    assert no_heading.sections[0].section_type == "unclassified"
    one_number = BookStructureSegmenter().segment_text("1\n\nText", source_name="fixture.txt")
    assert all(section.heading is None for section in one_number.sections)
    sequence = BookStructureSegmenter().segment_text(
        "1\n\nA\n\n2\n\nB", source_name="fixture.txt"
    )
    assert sum(section.heading is not None for section in sequence.sections) == 2
    empty = BookStructureSegmenter().segment_text("", source_name="fixture.txt")
    empty_plan = BookChunkPlanner().plan(empty)
    assert empty.sections == () and empty_plan.chunks == ()
    assert empty_plan.reconstruct_text() == ""


def test_source_fingerprint_changes_for_newline_and_whitespace() -> None:
    segmenter = BookStructureSegmenter()
    base = segmenter.segment_text("Chapter 1\nText", source_name="fixture.txt")
    newline = segmenter.segment_text("Chapter 1\r\nText", source_name="fixture.txt")
    whitespace = segmenter.segment_text("Chapter 1\nText ", source_name="fixture.txt")
    assert len({base.source_content_fingerprint, newline.source_content_fingerprint, whitespace.source_content_fingerprint}) == 3
