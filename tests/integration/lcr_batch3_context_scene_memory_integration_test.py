from __future__ import annotations

import ast
import hashlib
import subprocess
from pathlib import Path

import core.character_memory_v2 as cm2
import core.context_scene_memory as csm


ROOT = Path(__file__).resolve().parents[2]
T0 = "2026-07-16T00:00:00Z"
T1 = "2026-07-16T00:01:00Z"


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def evidence(kind=csm.EvidenceType.SOURCE_OBSERVATION, segment="seg-1"):
    kwargs = {"source_text_hash": sha("source:" + segment)}
    if kind == csm.EvidenceType.TRANSLATION_OBSERVATION:
        kwargs = {"translation_text_hash": sha("translation:" + segment)}
    return csm.create_context_evidence(evidence_type=kind, source_case_id="case-1", source_segment_id=segment, excerpt="受控證據", language="ko", observed_at=T0, **kwargs)


def character_store():
    store = cm2.MemoryStore()
    ev = cm2.create_evidence(evidence_type=cm2.EvidenceType.HUMAN_APPROVED, source_case_id="case-1", source_segment_id="seg-name", source_text_hash=sha("character"), excerpt="核准姓名", language="ko", observed_at=T0)
    record = cm2.create_memory(character_id="char-1", fact_type=cm2.FactType.CANONICAL_NAME, value="核准姓名", evidence=ev, confidence=.9, approval_status=cm2.ApprovalStatus.APPROVED, approval_metadata=cm2.ApprovalMetadata("核准姓名", T0, "reviewer", "decision-1"), created_at=T0)
    cm2.add_or_merge_memory(store, record, now=T0)
    return store


def test_end_to_end_offline_scene_character_selection_contract():
    char_store = character_store()
    store = csm.ContextMemoryStore()
    csm.add_scene(store, csm.create_scene_memory(scene_id="scene-1", chapter_id="chapter-1", evidence=evidence(), created_at=T0))
    participant = csm.link_character_memory(char_store, character_id="char-1", participant_status="present", presence_confidence=.95, evidence_reference="ev-participant")
    csm.add_scene_participant(store, "scene-1", character_id=participant.character_id, participant_status=participant.participant_status, presence_confidence=participant.presence_confidence, evidence_reference=participant.evidence_reference, memory_version=participant.memory_version, unresolved_identity=participant.unresolved_identity, updated_at=T1)
    record = csm.create_context_memory(context_type="source_context_excerpt", value="目前場景的短前文", evidence=evidence(), confidence=.95, chapter_id="chapter-1", scene_id="scene-1", sequence_index=3, created_at=T0)
    csm.add_or_merge_context(store, record, now=T0)
    view = csm.build_character_context_view(char_store, character_ids=("char-1",), token_budget=32, now=T1)
    selected = csm.select_context_for_translation(store, chapter_id="chapter-1", scene_id="scene-1", sequence_index=4, character_ids=("char-1",), token_budget=64, character_context_view=view, character_token_budget=32, now=T1)
    assert {item.item_type for item in selected.selected_records} == {"source_context_excerpt", "scene_participant"}
    assert [item.value for item in selected.selected_character_memories] == ["核准姓名"]
    assert selected.estimated_tokens <= 64 and selected.character_estimated_tokens <= 32


def test_character_memory_store_is_read_only_during_interoperability():
    store = character_store()
    before = cm2.serialize_memory_store(store)
    participant = csm.link_character_memory(store, character_id="char-1", participant_status="present", presence_confidence=.9, evidence_reference="ev")
    assert csm.resolve_scene_participant_reference(store, participant)
    assert cm2.serialize_memory_store(store) == before


def test_unresolved_identity_is_not_force_mapped():
    store = character_store()
    participant = csm.SceneParticipant("char-1", 1, csm.ParticipantStatus.PRESENT, .9, "ev", True)
    assert csm.resolve_scene_participant_reference(store, participant) == ()


def test_previous_translation_never_displaces_source_observation():
    store = csm.ContextMemoryStore()
    translated = csm.create_context_memory(context_type="previous_translation_excerpt", value="譯文線索", evidence=evidence(csm.EvidenceType.TRANSLATION_OBSERVATION, "tr"), confidence=.99, chapter_id="chapter-1", scene_id="scene-1", sequence_index=3, created_at=T0)
    source = csm.create_context_memory(context_type="source_context_excerpt", value="原文線索", evidence=evidence(segment="src"), confidence=.9, chapter_id="chapter-1", scene_id="scene-1", sequence_index=3, created_at=T0)
    csm.add_or_merge_context(store, translated, now=T0); csm.add_or_merge_context(store, source, now=T0)
    result = csm.select_context_for_translation(store, chapter_id="chapter-1", scene_id="scene-1", sequence_index=4, token_budget=7, now=T1)
    assert [item.value for item in result.selected_records] == ["原文線索"]


def test_round_trip_uses_only_temporary_directory(tmp_path):
    store = csm.ContextMemoryStore(); csm.add_scene(store, csm.create_scene_memory(scene_id="scene-1", chapter_id="chapter-1", evidence=evidence(), created_at=T0))
    target = tmp_path / "context-store.json"
    csm.save_context_store(target, store)
    assert csm.load_context_store(target).to_dict() == store.to_dict()


def test_core_has_no_runtime_provider_prompt_or_network_dependencies():
    forbidden_roots = {"requests", "httpx", "urllib", "socket"}
    forbidden_fragments = ("provider", "runtime", "prompt", "translation_pipeline")
    for path in (ROOT / "core" / "context_scene_memory").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): imports.extend(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom): imports.append(node.module or "")
        assert not forbidden_roots & {name.split(".")[0] for name in imports}
        assert not any(fragment in name.lower() for name in imports for fragment in forbidden_fragments)


def test_character_memory_v2_tracked_core_matches_head():
    for path in sorted((ROOT / "core" / "character_memory_v2").glob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        head = subprocess.run(["git", "show", f"HEAD:{relative}"], cwd=ROOT, check=True, capture_output=True).stdout
        assert path.read_bytes() == head


def test_batch3_changes_stay_inside_allowlist():
    status = subprocess.run(["git", "status", "--short"], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
    allowed = ("core/context_scene_memory/", "tests/unit/test_context_scene_memory.py", "tests/integration/lcr_batch3_context_scene_memory_integration_test.py", "ntpe_lcr_batch3_context_scene_memory_test.py", "audits/legacy_capability_recovery/batch3/")
    for line in status:
        path = line[3:].replace("\\", "/")
        assert path.startswith(allowed), path


def test_schema_versions_are_not_confused():
    assert csm.SCHEMA_VERSION == "1.0"
    assert cm2.SCHEMA_VERSION == "2.0"
