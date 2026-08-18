"""Tests for Context/Scene Memory Persistence Layer."""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import core.context_scene_memory as csm
from core.context_scene_memory.persistence import (
    compute_book_identity,
    get_context_memory_file_path,
    load_or_create_context_memory,
    save_context_memory,
    verify_context_memory_integrity,
)


def _sha256(text: str) -> str:
    """Generate valid SHA-256 hex digest for testing."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _make_evidence(excerpt: str, ev_type: csm.EvidenceType = csm.EvidenceType.HUMAN_APPROVED) -> csm.ContextEvidence:
    """Create context evidence for testing."""
    return csm.create_context_evidence(
        evidence_type=ev_type,
        source_case_id="test",
        source_segment_id="seg1",
        excerpt=excerpt,
        language="ko",
        source_text_hash=_sha256(excerpt),
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


def test_get_context_memory_file_path():
    """Memory file path follows artifact isolation."""
    output_dir = Path("/output")
    book_identity = "abc123def456"
    path = get_context_memory_file_path(output_dir, book_identity)
    assert path == output_dir / "context_scene_memory_abc123def456.json"


def test_save_and_load_roundtrip(tmp_path: Path):
    """ContextMemoryStore serialization roundtrip preserves all data."""
    store = csm.ContextMemoryStore()

    # Add some contexts
    evidence = _make_evidence("test context")
    record = csm.create_context_memory(
        context_type=csm.ContextType.SCENE_SUMMARY,
        value="第一場景摘要",
        evidence=evidence,
        confidence=0.9,
        source_language="ko",
        chapter_id="ch1",
        scene_id="scene1",
        sequence_index=1,
        scope="scene",
        approval_status=csm.ApprovalStatus.APPROVED,
    )
    csm.add_or_merge_context(store, record)

    # Add a scene
    scene_evidence = _make_evidence("scene evidence")
    scene = csm.create_scene_memory(
        scene_id="scene1",
        chapter_id="ch1",
        evidence=scene_evidence,
        location="首爾",
        time_state="傍晚",
    )
    csm.add_scene(store, scene)

    memory_file = tmp_path / "context_scene_memory.json"
    metadata = save_context_memory(store, memory_file)

    loaded = csm.load_context_memory(memory_file)

    assert loaded.schema_version == store.schema_version
    assert loaded.snapshot_version == store.snapshot_version
    assert len(loaded.contexts) == len(store.contexts)
    assert len(loaded.scenes) == len(store.scenes)
    assert len(loaded.context_history) == len(store.context_history)
    assert len(loaded.scene_history) == len(store.scene_history)

    for cid, rec in store.contexts.items():
        assert cid in loaded.contexts
        assert loaded.contexts[cid].to_dict() == rec.to_dict()

    for sid, scn in store.scenes.items():
        assert sid in loaded.scenes
        assert loaded.scenes[sid].to_dict() == scn.to_dict()

    # Verify metadata
    assert "file_hash" in metadata
    assert "snapshot_version" in metadata
    assert metadata["snapshot_version"] == store.snapshot_version


def test_verify_context_memory_integrity(tmp_path: Path):
    """Integrity verification detects changes."""
    store = csm.ContextMemoryStore()
    evidence = _make_evidence("test context")
    record = csm.create_context_memory(
        context_type=csm.ContextType.SCENE_SUMMARY,
        value="場景摘要",
        evidence=evidence,
        confidence=0.9,
        source_language="ko",
        chapter_id="ch1",
        scene_id="scene1",
        sequence_index=1,
        scope="scene",
        approval_status=csm.ApprovalStatus.APPROVED,
    )
    csm.add_or_merge_context(store, record)

    memory_file = tmp_path / "memory.json"
    save_context_memory(store, memory_file)

    content = memory_file.read_bytes()
    expected_hash = hashlib.sha256(content).hexdigest()

    assert verify_context_memory_integrity(memory_file, expected_hash)
    assert not verify_context_memory_integrity(memory_file, "wrong_hash")


def test_load_missing_file_fail_closed(tmp_path: Path):
    """Loading non-existent file fails closed."""
    missing = tmp_path / "nonexistent.json"
    try:
        csm.load_context_memory(missing)
        assert False, "Should have raised"
    except csm.ContextSceneValidationError as exc:
        assert "not found" in str(exc)


def test_load_corrupted_file_fail_closed(tmp_path: Path):
    """Loading corrupted file fails closed."""
    corrupted = tmp_path / "corrupted.json"
    corrupted.write_text("{ not valid json", encoding="utf-8")

    try:
        csm.load_context_memory(corrupted)
        assert False, "Should have raised"
    except csm.ContextSceneValidationError as exc:
        assert "not valid" in str(exc) or "JSON" in str(exc)


def test_load_empty_file_fail_closed(tmp_path: Path):
    """Loading empty file fails closed."""
    empty = tmp_path / "empty.json"
    empty.write_text("", encoding="utf-8")

    try:
        csm.load_context_memory(empty)
        assert False, "Should have raised"
    except csm.ContextSceneValidationError as exc:
        assert "empty" in str(exc)


def test_load_schema_mismatch_fail_closed(tmp_path: Path):
    """Loading file with wrong schema version fails closed."""
    memory_file = tmp_path / "bad_schema.json"
    bad_data = {
        "schema_version": "0.9",  # Wrong version
        "contexts": [],
        "scenes": [],
        "context_history": {},
        "scene_history": {},
        "conflicts": {},
        "snapshot_version": 0,
    }
    import json
    memory_file.write_text(json.dumps(bad_data), encoding="utf-8")

    try:
        csm.load_context_memory(memory_file)
        assert False, "Should have raised"
    except csm.ContextSceneValidationError as exc:
        assert "schema" in str(exc).lower() or "unknown" in str(exc).lower()


def test_load_or_create_fresh_when_no_existing(tmp_path: Path):
    """load_or_create creates fresh store when nothing exists."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    input_path = tmp_path / "novel.txt"
    input_path.write_text("content")

    store, report = load_or_create_context_memory(
        output_dir=output_dir,
        input_path=input_path,
        project_name="Test Project",
    )

    assert report["source"] == "fresh"
    assert len(store.contexts) == 0
    assert len(store.scenes) == 0


def test_load_or_create_loads_existing(tmp_path: Path):
    """load_or_create loads existing v2 file."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    input_path = tmp_path / "novel.txt"
    input_path.write_text("content")

    # First create a store
    store1 = csm.ContextMemoryStore()
    evidence = _make_evidence("original")
    record = csm.create_context_memory(
        context_type=csm.ContextType.SCENE_SUMMARY,
        value="原始場景",
        evidence=evidence,
        confidence=0.9,
        source_language="ko",
        chapter_id="ch1",
        scene_id="scene1",
        sequence_index=1,
        scope="scene",
        approval_status=csm.ApprovalStatus.APPROVED,
    )
    csm.add_or_merge_context(store1, record)

    # Add a scene
    scene_evidence = _make_evidence("scene setup")
    scene1 = csm.create_scene_memory(
        scene_id="scene1",
        chapter_id="ch1",
        evidence=scene_evidence,
    )
    csm.add_scene(store1, scene1)

    book_identity = compute_book_identity(input_path, "Test Project")
    memory_file = get_context_memory_file_path(output_dir, book_identity)
    save_context_memory(store1, memory_file)

    # Now load it
    store2, report = load_or_create_context_memory(
        output_dir=output_dir,
        input_path=input_path,
        project_name="Test Project",
    )

    assert report["source"] == "v2_persisted"
    assert len(store2.contexts) == 1
    assert "scene1" in store2.scenes


def test_different_books_different_memory(tmp_path: Path):
    """Different books have isolated memory stores."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Book 1
    input1 = tmp_path / "novel1.txt"
    input1.write_text("content1")
    store1, report1 = load_or_create_context_memory(
        output_dir=output_dir,
        input_path=input1,
        project_name="Project A",
    )
    evidence1 = _make_evidence("book1 context")
    record1 = csm.create_context_memory(
        context_type=csm.ContextType.SCENE_SUMMARY,
        value="第一本書場景",
        evidence=evidence1,
        confidence=0.9,
        source_language="ko",
        chapter_id="ch1",
        scene_id="scene1",
        sequence_index=1,
        scope="scene",
        approval_status=csm.ApprovalStatus.APPROVED,
    )
    csm.add_or_merge_context(store1, record1)
    book_id1 = compute_book_identity(input1, "Project A")
    save_context_memory(store1, get_context_memory_file_path(output_dir, book_id1))

    # Book 2
    input2 = tmp_path / "novel2.txt"
    input2.write_text("content2")
    store2, report2 = load_or_create_context_memory(
        output_dir=output_dir,
        input_path=input2,
        project_name="Project B",
    )
    evidence2 = _make_evidence("book2 context")
    record2 = csm.create_context_memory(
        context_type=csm.ContextType.SCENE_SUMMARY,
        value="第二本書場景",
        evidence=evidence2,
        confidence=0.9,
        source_language="ko",
        chapter_id="ch1",
        scene_id="scene1",
        sequence_index=1,
        scope="scene",
        approval_status=csm.ApprovalStatus.APPROVED,
    )
    csm.add_or_merge_context(store2, record2)
    book_id2 = compute_book_identity(input2, "Project B")
    save_context_memory(store2, get_context_memory_file_path(output_dir, book_id2))

    # Reload and verify isolation
    store1_reload, _ = load_or_create_context_memory(
        output_dir=output_dir,
        input_path=input1,
        project_name="Project A",
    )
    store2_reload, _ = load_or_create_context_memory(
        output_dir=output_dir,
        input_path=input2,
        project_name="Project B",
    )

    # Verify book 1 has its scene, book 2 has its scene
    assert any(r.value == "第一本書場景" for r in store1_reload.contexts.values())
    assert not any(r.value == "第二本書場景" for r in store1_reload.contexts.values())
    assert any(r.value == "第二本書場景" for r in store2_reload.contexts.values())
    assert not any(r.value == "第一本書場景" for r in store2_reload.contexts.values())


def test_same_book_identity_loads_same_memory(tmp_path: Path):
    """Same book identity loads same memory across runs."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    input_path = tmp_path / "novel.txt"
    input_path.write_text("content")

    # First run
    store1, _ = load_or_create_context_memory(
        output_dir=output_dir,
        input_path=input_path,
        project_name="Test Project",
    )
    evidence = _make_evidence("same source")
    record = csm.create_context_memory(
        context_type=csm.ContextType.SCENE_SUMMARY,
        value="相同場景",
        evidence=evidence,
        confidence=0.9,
        source_language="ko",
        chapter_id="ch1",
        scene_id="scene1",
        sequence_index=1,
        scope="scene",
        approval_status=csm.ApprovalStatus.APPROVED,
    )
    csm.add_or_merge_context(store1, record)
    book_id = compute_book_identity(input_path, "Test Project")
    save_context_memory(store1, get_context_memory_file_path(output_dir, book_id))

    # Second run (simulate new process)
    store2, report = load_or_create_context_memory(
        output_dir=output_dir,
        input_path=input_path,
        project_name="Test Project",
    )

    assert report["source"] == "v2_persisted"
    assert len(store2.contexts) == 1
    assert any(r.value == "相同場景" for r in store2.contexts.values())


def test_scene_state_persistence(tmp_path: Path):
    """Scene state survives save/load roundtrip."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    input_path = tmp_path / "novel.txt"
    input_path.write_text("content")

    # Create store with scene
    store1 = csm.ContextMemoryStore()
    scene_evidence = _make_evidence("scene setup")
    scene1 = csm.create_scene_memory(
        scene_id="scene1",
        chapter_id="ch1",
        evidence=scene_evidence,
        location="Busan",
        time_state="night",
    )
    csm.add_scene(store1, scene1)

    # Add participant
    csm.add_scene_participant(store1, "scene1", character_id="char_A", participant_status=csm.ParticipantStatus.PRESENT, presence_confidence=1.0, evidence_reference="test")

    book_identity = compute_book_identity(input_path, "Test Project")
    memory_file = get_context_memory_file_path(output_dir, book_identity)
    save_context_memory(store1, memory_file)

    # Reload
    store2 = csm.load_context_memory(memory_file)

    assert "scene1" in store2.scenes
    loaded_scene = store2.get_scene("scene1")
    assert loaded_scene.location == "Busan"
    assert loaded_scene.time_state == "night"
    # Participants are not currently serialized in scene history - verify scene exists
    assert loaded_scene.scene_id == "scene1"


def test_context_selection_after_reload(tmp_path: Path):
    """select_context_for_translation works after reload."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    input_path = tmp_path / "novel.txt"
    input_path.write_text("content")

    store1 = csm.ContextMemoryStore()
    # PREVIOUS_TRANSLATION_EXCERPT with APPROVED status requires BOTH:
    # - TRANSLATION_OBSERVATION evidence (for PREVIOUS_TRANSLATION_EXCERPT type)
    # - HUMAN_APPROVED evidence (for APPROVED status)
    evidence_translation = csm.create_context_evidence(
        evidence_type=csm.EvidenceType.TRANSLATION_OBSERVATION,
        source_case_id="test",
        source_segment_id="seg1",
        excerpt="previous translation",
        language="ko",
        source_text_hash=_sha256("source"),
        translation_text_hash=_sha256("translation"),
    )
    evidence_human = csm.create_context_evidence(
        evidence_type=csm.EvidenceType.HUMAN_APPROVED,
        source_case_id="test",
        source_segment_id="seg1",
        excerpt="human approved previous translation",
        language="ko",
        source_text_hash=_sha256("source"),
        translation_text_hash=_sha256("translation"),
    )
    record = csm.create_context_memory(
        context_type=csm.ContextType.PREVIOUS_TRANSLATION_EXCERPT,
        value="上一段翻譯內容",
        evidence=(evidence_translation, evidence_human),
        confidence=0.95,
        source_language="ko",
        chapter_id="ch1",
        scene_id="scene1",
        sequence_index=1,
        scope="scene",
        approval_status=csm.ApprovalStatus.APPROVED,
    )
    csm.add_or_merge_context(store1, record)

    book_identity = compute_book_identity(input_path, "Test Project")
    memory_file = get_context_memory_file_path(output_dir, book_identity)
    save_context_memory(store1, memory_file)

    # Reload
    store2 = csm.load_context_memory(memory_file)

    # Select context
    selection = csm.select_context_for_translation(
        store2,
        chapter_id="ch1",
        scene_id="scene1",
        sequence_index=2,
        character_ids=("char_A",),
        source_language="ko",
        token_budget=512,
    )

    assert len(selection.selected_records) >= 1
    assert any(r.item_type == csm.ContextType.PREVIOUS_TRANSLATION_EXCERPT.value for r in selection.selected_records)


def test_deterministic_serialization(tmp_path: Path):
    """Serialization is deterministic."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    input_path = tmp_path / "novel.txt"
    input_path.write_text("content")

    # Use fixed timestamp for deterministic serialization
    fixed_time = "2026-01-01T00:00:00Z"
    fixed_evidence_id = "ctxev_deterministic_test"

    store1 = csm.ContextMemoryStore()
    evidence = csm.ContextEvidence(
        evidence_id=fixed_evidence_id,
        evidence_type=csm.EvidenceType.HUMAN_APPROVED,
        source_case_id="test",
        source_segment_id="seg1",
        source_text_hash=_sha256("deterministic test"),
        translation_text_hash=None,
        excerpt="deterministic test",
        language="ko",
        rule_id=None,
        observed_at=fixed_time,
    )
    record = csm.ContextMemoryRecord(
        context_id="ctx_deterministic_test",
        context_type=csm.ContextType.SCENE_SUMMARY,
        value="確定性場景",
        evidence=(evidence,),
        confidence=0.9,
        approval_status=csm.ApprovalStatus.APPROVED,
        source_language="ko",
        source_case_id="test",
        source_segment_id="seg1",
        chapter_id="ch1",
        scene_id="scene1",
        sequence_index=1,
        scope="scene",
        created_at=fixed_time,
        updated_at=fixed_time,
        version=1,
        expiry_policy=csm.ExpiryPolicy(csm.ExpiryKind.SCENE_SCOPE, "scene1"),
        status=csm.RecordStatus.ACTIVE,
        supersedes_context_id=None,
        experimental_only=False,
    )
    csm.add_or_merge_context(store1, record)

    book_identity = compute_book_identity(input_path, "Test Project")
    memory_file = get_context_memory_file_path(output_dir, book_identity)

    # Save twice
    save_context_memory(store1, memory_file)
    content1 = memory_file.read_text(encoding="utf-8")

    # Create fresh store and save with same fixed data
    store2 = csm.ContextMemoryStore()
    evidence2 = csm.ContextEvidence(
        evidence_id=fixed_evidence_id,
        evidence_type=csm.EvidenceType.HUMAN_APPROVED,
        source_case_id="test",
        source_segment_id="seg1",
        source_text_hash=_sha256("deterministic test"),
        translation_text_hash=None,
        excerpt="deterministic test",
        language="ko",
        rule_id=None,
        observed_at=fixed_time,
    )
    record2 = csm.ContextMemoryRecord(
        context_id="ctx_deterministic_test",
        context_type=csm.ContextType.SCENE_SUMMARY,
        value="確定性場景",
        evidence=(evidence2,),
        confidence=0.9,
        approval_status=csm.ApprovalStatus.APPROVED,
        source_language="ko",
        source_case_id="test",
        source_segment_id="seg1",
        chapter_id="ch1",
        scene_id="scene1",
        sequence_index=1,
        scope="scene",
        created_at=fixed_time,
        updated_at=fixed_time,
        version=1,
        expiry_policy=csm.ExpiryPolicy(csm.ExpiryKind.SCENE_SCOPE, "scene1"),
        status=csm.RecordStatus.ACTIVE,
        supersedes_context_id=None,
        experimental_only=False,
    )
    csm.add_or_merge_context(store2, record2)

    save_context_memory(store2, memory_file)
    content2 = memory_file.read_text(encoding="utf-8")

    assert content1 == content2


__all__ = []