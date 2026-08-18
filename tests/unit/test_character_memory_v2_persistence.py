"""Tests for Character Memory v2 Persistence Layer."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import core.character_memory_v2 as cm
from core.character_memory_v2.persistence import (
    compute_book_identity,
    get_memory_file_path,
    load_or_create_character_memory,
    migrate_lts_to_v2,
    save_character_memory,
    verify_memory_integrity,
)


def _sha256(text: str) -> str:
    """Generate valid SHA-256 hex digest for testing."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _make_approval_metadata(approved_value: str) -> cm.ApprovalMetadata:
    """Create approval metadata for approved memories."""
    return cm.ApprovalMetadata(
        approved_value=approved_value,
        approved_at="2026-01-01T00:00:00Z",
        reviewer="test_reviewer",
        decision_reference="test_decision",
    )


def test_compute_book_identity_deterministic():
    """Book identity must be deterministic for same input."""
    input_path = Path("/test/novel.txt")
    project_name = "Test Project"

    id1 = compute_book_identity(input_path, project_name)
    id2 = compute_book_identity(input_path, project_name)
    assert id1 == id2
    assert len(id1) == 16


def test_compute_book_identity_different_inputs():
    """Different inputs must produce different identities."""
    id1 = compute_book_identity(Path("/test/novel1.txt"), "Project A")
    id2 = compute_book_identity(Path("/test/novel2.txt"), "Project A")
    id3 = compute_book_identity(Path("/test/novel1.txt"), "Project B")
    assert id1 != id2
    assert id1 != id3


def test_get_memory_file_path():
    """Memory file path follows artifact isolation."""
    output_dir = Path("/output")
    book_identity = "abc123def456"
    path = get_memory_file_path(output_dir, book_identity)
    assert path == output_dir / "character_memory_abc123def456.json"


def test_save_and_load_roundtrip(tmp_path: Path):
    """MemoryStore serialization roundtrip preserves all data."""
    store = cm.MemoryStore()

    # Add some memories
    record1 = cm.create_memory(
        character_id="char_1",
        fact_type=cm.FactType.CANONICAL_NAME,
        value="測試角色",
        evidence=cm.create_evidence(
            evidence_type=cm.EvidenceType.HUMAN_APPROVED,
            source_case_id="test",
            source_segment_id="seg1",
            source_text_hash=_sha256("test source"),
            excerpt="테스트",
            language="ko",
        ),
        confidence=0.95,
        approval_status=cm.ApprovalStatus.APPROVED,
        approval_metadata=_make_approval_metadata("測試角色"),
    )
    cm.add_or_merge_memory(store, record1)

    memory_file = tmp_path / "character_memory.json"
    metadata = save_character_memory(store, memory_file)

    loaded = cm.load_character_memory(memory_file)

    assert loaded.schema_version == store.schema_version
    assert loaded.snapshot_version == store.snapshot_version
    assert len(loaded.records) == len(store.records)
    for mid, rec in store.records.items():
        assert mid in loaded.records
        assert loaded.records[mid].to_dict() == rec.to_dict()

    # Verify metadata
    assert "file_hash" in metadata
    assert "snapshot_version" in metadata
    assert metadata["snapshot_version"] == store.snapshot_version


def test_verify_memory_integrity(tmp_path: Path):
    """Integrity verification detects changes."""
    store = cm.MemoryStore()
    record = cm.create_memory(
        character_id="char_1",
        fact_type=cm.FactType.CANONICAL_NAME,
        value="角色A",
        evidence=cm.create_evidence(
            evidence_type=cm.EvidenceType.HUMAN_APPROVED,
            source_case_id="test",
            source_segment_id="seg1",
            source_text_hash=_sha256("source text"),
            excerpt="원문",
            language="ko",
        ),
        confidence=0.9,
        approval_status=cm.ApprovalStatus.APPROVED,
        approval_metadata=_make_approval_metadata("角色A"),
    )
    cm.add_or_merge_memory(store, record)

    memory_file = tmp_path / "memory.json"
    save_character_memory(store, memory_file)

    content = memory_file.read_bytes()
    expected_hash = hashlib.sha256(content).hexdigest()

    assert verify_memory_integrity(memory_file, expected_hash)
    assert not verify_memory_integrity(memory_file, "wrong_hash")


def test_load_missing_file_fail_closed(tmp_path: Path):
    """Loading non-existent file fails closed."""
    missing = tmp_path / "nonexistent.json"
    try:
        cm.load_character_memory(missing)
        assert False, "Should have raised"
    except cm.CharacterMemoryValidationError as exc:
        assert "not found" in str(exc)


def test_load_corrupted_file_fail_closed(tmp_path: Path):
    """Loading corrupted file fails closed."""
    corrupted = tmp_path / "corrupted.json"
    corrupted.write_text("{ not valid json", encoding="utf-8")

    try:
        cm.load_character_memory(corrupted)
        assert False, "Should have raised"
    except cm.CharacterMemoryValidationError as exc:
        assert "not valid" in str(exc) or "JSON" in str(exc)


def test_load_empty_file_fail_closed(tmp_path: Path):
    """Loading empty file fails closed."""
    empty = tmp_path / "empty.json"
    empty.write_text("", encoding="utf-8")

    try:
        cm.load_character_memory(empty)
        assert False, "Should have raised"
    except cm.CharacterMemoryValidationError as exc:
        assert "empty" in str(exc)


def test_migrate_lts_to_v2(tmp_path: Path):
    """LTS migration produces valid v2 store."""
    lts_path = tmp_path / "character_memory_lts.json"
    lts_data = {
        "version": "1.1-lts-stage-03",
        "updated_at": "2026-07-11T22:26:20",
        "characters": {
            "정태的": "鄭泰義",
            "카일": "凱爾",
            "일레이": "伊萊",
        },
    }
    lts_path.write_text(json.dumps(lts_data, ensure_ascii=False), encoding="utf-8")

    output_dir = tmp_path / "output"
    output_dir.mkdir()
    book_identity = "test_book_123"

    store, report = migrate_lts_to_v2(lts_path, output_dir, book_identity)

    assert report["success"]
    assert report["migrated"] == 3
    assert report["skipped"] == 0
    assert len(report["errors"]) == 0

    # Verify store has correct records
    assert len(store.records) == 3
    for rec in store.records.values():
        assert rec.fact_type == cm.FactType.CANONICAL_NAME
        assert rec.approval_status == cm.ApprovalStatus.APPROVED
        assert rec.evidence_type == cm.EvidenceType.HISTORICAL_IMPORT
        assert rec.confidence == 1.0

    # Verify file was created
    memory_file = output_dir / f"character_memory_{book_identity}.json"
    assert memory_file.exists()

    # Verify original LTS preserved
    assert lts_path.exists()
    original = json.loads(lts_path.read_text(encoding="utf-8"))
    assert original == lts_data


def test_migrate_lts_to_v2_deterministic(tmp_path: Path):
    """Migration is deterministic - same input produces same output."""
    lts_path = tmp_path / "character_memory_lts.json"
    lts_data = {
        "version": "1.1-lts-stage-03",
        "updated_at": "2026-07-11T22:26:20",
        "characters": {
            "정태的": "鄭泰義",
            "카일": "凱爾",
        },
    }
    lts_path.write_text(json.dumps(lts_data, ensure_ascii=False), encoding="utf-8")

    output_dir = tmp_path / "output"
    output_dir.mkdir()
    book_identity = "test_deterministic"

    store1, _ = migrate_lts_to_v2(lts_path, output_dir, book_identity)
    store2, _ = migrate_lts_to_v2(lts_path, output_dir, book_identity)

    # Both stores should have identical content
    assert len(store1.records) == len(store2.records)
    for mid1, rec1 in sorted(store1.records.items()):
        mid2 = sorted(store2.records.keys())[list(sorted(store1.records.keys())).index(mid1)]
        assert rec1.to_dict() == store2.records[mid2].to_dict()


def test_migrate_lts_preserves_original(tmp_path: Path):
    """Original LTS file is never modified."""
    lts_path = tmp_path / "character_memory_lts.json"
    lts_data = {
        "version": "1.1-lts-stage-03",
        "updated_at": "2026-07-11T22:26:20",
        "characters": {
            "정태的": "鄭泰義",
        },
    }
    lts_path.write_text(json.dumps(lts_data, ensure_ascii=False), encoding="utf-8")

    output_dir = tmp_path / "output"
    output_dir.mkdir()
    book_identity = "test_preserve"

    migrate_lts_to_v2(lts_path, output_dir, book_identity)

    # Original unchanged
    current = json.loads(lts_path.read_text(encoding="utf-8"))
    assert current == lts_data


def test_migrate_lts_invalid_json_fail_closed(tmp_path: Path):
    """Invalid LTS JSON fails closed."""
    lts_path = tmp_path / "bad.json"
    lts_path.write_text("{ invalid", encoding="utf-8")

    output_dir = tmp_path / "output"
    output_dir.mkdir()
    book_identity = "test_bad"

    try:
        migrate_lts_to_v2(lts_path, output_dir, book_identity)
        assert False, "Should have raised"
    except cm.CharacterMemoryValidationError as exc:
        assert "not valid JSON" in str(exc)


def test_migrate_lts_missing_characters_fail_closed(tmp_path: Path):
    """LTS without characters object fails closed."""
    lts_path = tmp_path / "no_chars.json"
    lts_path.write_text(json.dumps({"version": "1.0"}), encoding="utf-8")

    output_dir = tmp_path / "output"
    output_dir.mkdir()
    book_identity = "test_no_chars"

    try:
        migrate_lts_to_v2(lts_path, output_dir, book_identity)
        assert False, "Should have raised"
    except cm.CharacterMemoryValidationError as exc:
        assert "characters" in str(exc)


def test_load_or_create_from_v2(tmp_path: Path):
    """load_or_create loads existing v2 file."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    input_path = tmp_path / "novel.txt"
    input_path.write_text("content")

    # First create a store
    store1 = cm.MemoryStore()
    record = cm.create_memory(
        character_id="char_1",
        fact_type=cm.FactType.CANONICAL_NAME,
        value="角色",
        evidence=cm.create_evidence(
            evidence_type=cm.EvidenceType.HUMAN_APPROVED,
            source_case_id="test",
            source_segment_id="seg1",
            source_text_hash=_sha256("source"),
            excerpt="원문",
            language="ko",
        ),
        confidence=0.9,
        approval_status=cm.ApprovalStatus.APPROVED,
        approval_metadata=_make_approval_metadata("角色"),
    )
    cm.add_or_merge_memory(store1, record)

    book_identity = compute_book_identity(input_path, "Test Project")
    memory_file = get_memory_file_path(output_dir, book_identity)
    save_character_memory(store1, memory_file)

    # Now load it
    store2, report = load_or_create_character_memory(
        output_dir=output_dir,
        input_path=input_path,
        project_name="Test Project",
    )

    assert report["source"] == "v2_persisted"
    assert len(store2.records) == 1
    assert report["migration_report"] is None


def test_load_or_create_from_lts_migration(tmp_path: Path):
    """load_or_create migrates from LTS when no v2 file exists."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    input_path = tmp_path / "novel.txt"
    input_path.write_text("content")

    lts_path = tmp_path / "character_memory_lts.json"
    lts_data = {
        "version": "1.1-lts-stage-03",
        "updated_at": "2026-07-11T22:26:20",
        "characters": {
            "정태的": "鄭泰義",
        },
    }
    lts_path.write_text(json.dumps(lts_data, ensure_ascii=False), encoding="utf-8")

    store, report = load_or_create_character_memory(
        output_dir=output_dir,
        input_path=input_path,
        project_name="Test Project",
        lts_path=lts_path,
    )

    assert report["source"] == "lts_migration"
    assert report["migration_report"]["success"]
    assert len(store.records) == 1


def test_load_or_create_fresh_when_no_existing(tmp_path: Path):
    """load_or_create creates fresh store when nothing exists."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    input_path = tmp_path / "novel.txt"
    input_path.write_text("content")

    store, report = load_or_create_character_memory(
        output_dir=output_dir,
        input_path=input_path,
        project_name="Test Project",
        lts_path=None,
    )

    assert report["source"] == "fresh"
    assert len(store.records) == 0


def test_load_or_create_prefers_v2_over_lts(tmp_path: Path):
    """Existing v2 file takes precedence over LTS."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    input_path = tmp_path / "novel.txt"
    input_path.write_text("content")

    # Create v2 file
    book_identity = compute_book_identity(input_path, "Test Project")
    memory_file = get_memory_file_path(output_dir, book_identity)
    store1 = cm.MemoryStore()
    record = cm.create_memory(
        character_id="char_v2",
        fact_type=cm.FactType.CANONICAL_NAME,
        value="從V2載入",
        evidence=cm.create_evidence(
            evidence_type=cm.EvidenceType.HUMAN_APPROVED,
            source_case_id="test",
            source_segment_id="seg1",
            source_text_hash=_sha256("v2 source"),
            excerpt="원문",
            language="ko",
        ),
        confidence=0.9,
        approval_status=cm.ApprovalStatus.APPROVED,
        approval_metadata=_make_approval_metadata("從V2載入"),
    )
    cm.add_or_merge_memory(store1, record)
    save_character_memory(store1, memory_file)

    # Also create LTS
    lts_path = tmp_path / "character_memory_lts.json"
    lts_data = {
        "version": "1.1-lts-stage-03",
        "updated_at": "2026-07-11T22:26:20",
        "characters": {
            "version": "1.1-lts-stage-03",
            "updated_at": "2026-07-07T01:31:15",
            "來自LTS": "LTS角色",
        },
    }
    lts_path.write_text(json.dumps(lts_data, ensure_ascii=False), encoding="utf-8")

    store2, report = load_or_create_character_memory(
        output_dir=output_dir,
        input_path=input_path,
        project_name="Test Project",
        lts_path=lts_path,
    )

    assert report["source"] == "v2_persisted"
    assert report["migration_report"] is None
    assert any(r.character_id == "char_v2" for r in store2.records.values())


def test_different_books_different_memory(tmp_path: Path):
    """Different books have isolated memory stores."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Book 1
    input1 = tmp_path / "novel1.txt"
    input1.write_text("content1")
    store1, report1 = load_or_create_character_memory(
        output_dir=output_dir,
        input_path=input1,
        project_name="Project A",
    )
    record1 = cm.create_memory(
        character_id="char1",
        fact_type=cm.FactType.CANONICAL_NAME,
        value="角色1",
        evidence=cm.create_evidence(
            evidence_type=cm.EvidenceType.HUMAN_APPROVED,
            source_case_id="test",
            source_segment_id="seg1",
            source_text_hash=_sha256("source1"),
            excerpt="원문1",
            language="ko",
        ),
        confidence=0.9,
        approval_status=cm.ApprovalStatus.APPROVED,
        approval_metadata=_make_approval_metadata("角色1"),
    )
    cm.add_or_merge_memory(store1, record1)
    book_id1 = compute_book_identity(input1, "Project A")
    save_character_memory(store1, get_memory_file_path(output_dir, book_id1))

    # Book 2
    input2 = tmp_path / "novel2.txt"
    input2.write_text("content2")
    store2, report2 = load_or_create_character_memory(
        output_dir=output_dir,
        input_path=input2,
        project_name="Project B",
    )
    record2 = cm.create_memory(
        character_id="char2",
        fact_type=cm.FactType.CANONICAL_NAME,
        value="角色2",
        evidence=cm.create_evidence(
            evidence_type=cm.EvidenceType.HUMAN_APPROVED,
            source_case_id="test",
            source_segment_id="seg1",
            source_text_hash=_sha256("source2"),
            excerpt="원문2",
            language="ko",
        ),
        confidence=0.9,
        approval_status=cm.ApprovalStatus.APPROVED,
        approval_metadata=_make_approval_metadata("角色2"),
    )
    cm.add_or_merge_memory(store2, record2)
    book_id2 = compute_book_identity(input2, "Project B")
    save_character_memory(store2, get_memory_file_path(output_dir, book_id2))

    # Reload and verify isolation
    store1_reload, _ = load_or_create_character_memory(
        output_dir=output_dir,
        input_path=input1,
        project_name="Project A",
    )
    store2_reload, _ = load_or_create_character_memory(
        output_dir=output_dir,
        input_path=input2,
        project_name="Project B",
    )

    assert any(r.character_id == "char1" for r in store1_reload.records.values())
    assert not any(r.character_id == "char2" for r in store1_reload.records.values())
    assert any(r.character_id == "char2" for r in store2_reload.records.values())
    assert not any(r.character_id == "char1" for r in store2_reload.records.values())


def test_same_book_identity_loads_same_memory(tmp_path: Path):
    """Same book identity loads same memory across runs."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    input_path = tmp_path / "novel.txt"
    input_path.write_text("content")

    # First run
    store1, _ = load_or_create_character_memory(
        output_dir=output_dir,
        input_path=input_path,
        project_name="Test Project",
    )
    record = cm.create_memory(
        character_id="char1",
        fact_type=cm.FactType.CANONICAL_NAME,
        value="角色",
        evidence=cm.create_evidence(
            evidence_type=cm.EvidenceType.HUMAN_APPROVED,
            source_case_id="test",
            source_segment_id="seg1",
            source_text_hash=_sha256("same source"),
            excerpt="원문",
            language="ko",
        ),
        confidence=0.9,
        approval_status=cm.ApprovalStatus.APPROVED,
        approval_metadata=_make_approval_metadata("角色"),
    )
    cm.add_or_merge_memory(store1, record)
    book_id = compute_book_identity(input_path, "Test Project")
    save_character_memory(store1, get_memory_file_path(output_dir, book_id))

    # Second run (simulate new process)
    store2, report = load_or_create_character_memory(
        output_dir=output_dir,
        input_path=input_path,
        project_name="Test Project",
    )

    assert report["source"] == "v2_persisted"
    assert len(store2.records) == 1
    assert any(r.character_id == "char1" for r in store2.records.values())


__all__ = []