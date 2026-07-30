from __future__ import annotations

import hashlib
import time

import core.character_memory_v2 as cm2
import core.context_scene_memory as csm


T0 = "2026-07-16T00:00:00Z"
T1 = "2026-07-16T00:01:00Z"


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def evidence(segment: str, kind=csm.EvidenceType.SOURCE_OBSERVATION):
    hashes = {"translation_text_hash": sha("tr:" + segment)} if kind == csm.EvidenceType.TRANSLATION_OBSERVATION else {"source_text_hash": sha("src:" + segment)}
    return csm.create_context_evidence(evidence_type=kind, source_case_id="root-case", source_segment_id=segment, excerpt="受控短證據", language="ko", observed_at=T0, **hashes)


def timed(operation):
    started = time.perf_counter()
    result = operation()
    return result, (time.perf_counter() - started) * 1000


def check(name: str, condition: bool):
    if not condition:
        print(f"FAIL {name}")
        raise AssertionError(name)
    print(f"PASS {name}")


def character_fixture():
    store = cm2.MemoryStore()
    ev = cm2.create_evidence(evidence_type=cm2.EvidenceType.HUMAN_APPROVED, source_case_id="root-case", source_segment_id="char-seg", source_text_hash=sha("character"), excerpt="人工核准姓名", language="ko", observed_at=T0)
    record = cm2.create_memory(character_id="char-1", fact_type=cm2.FactType.CANONICAL_NAME, value="人工核准姓名", evidence=ev, confidence=.9, approval_status=cm2.ApprovalStatus.APPROVED, approval_metadata=cm2.ApprovalMetadata("人工核准姓名", T0, "reviewer", "decision-root"), created_at=T0)
    cm2.add_or_merge_memory(store, record, now=T0)
    return store


def main():
    store = csm.ContextMemoryStore()
    csm.add_scene(store, csm.create_scene_memory(scene_id="scene-1", chapter_id="chapter-1", evidence=evidence("scene"), created_at=T0))

    def add_contexts():
        for index in range(100):
            record = csm.create_context_memory(context_type="other", value=f"上下文 {index}", evidence=evidence(f"ctx-{index}"), confidence=.95, chapter_id="chapter-1", scene_id="scene-1", sequence_index=index, created_at=T0)
            csm.add_or_merge_context(store, record, now=T0)
    _, add_ms = timed(add_contexts)
    check("100 context add/merge", len(store.contexts) == 100 and add_ms < 100)
    serialization_store = csm.ContextMemoryStore.from_dict(store.snapshot())

    def participants():
        for index in range(100):
            csm.add_scene_participant(store, "scene-1", character_id=f"char-{index}", participant_status="present", presence_confidence=.9, evidence_reference=f"ev-{index}", updated_at=T1)
    _, participant_ms = timed(participants)
    check("100 participant operations", len(store.get_scene("scene-1").participants) == 100 and participant_ms < 100)

    selected, selection_ms = timed(lambda: csm.select_context_for_translation(store, chapter_id="chapter-1", scene_id="scene-1", sequence_index=100, token_budget=512, now=T1))
    check("100-record context selection", selected.estimated_tokens <= 512 and selection_ms < 25)
    check("deterministic selection", selected.deterministic_fingerprint == csm.select_context_for_translation(store, chapter_id="chapter-1", scene_id="scene-1", sequence_index=100, token_budget=512, now=T1).deterministic_fingerprint)

    encoded, serialization_ms = timed(lambda: csm.serialize_context_store(serialization_store))
    restored, deserialize_ms = timed(lambda: csm.deserialize_context_store(encoded))
    serialization_total = serialization_ms + deserialize_ms
    print(f"BENCHMARK serialization_round_trip_ms={serialization_total:.3f}")
    check("serialization round trip", restored.to_dict() == serialization_store.to_dict() and serialization_total < 60)

    snapshot = store.snapshot()
    transition_result, transition_ms = timed(lambda: csm.transition_scene(store, from_scene_id="scene-1", boundary="scene_transition", to_scene_id="scene-2", evidence=evidence("transition"), transitioned_at="2026-07-16T00:02:00Z"))
    check("scene transition", transition_result["changed"] and transition_ms < 10)
    store.restore(snapshot)

    first = next(iter(store.contexts.values()))
    csm.expire_context(store, first.context_id, expired_at="2026-07-16T00:02:00Z")
    rolled, rollback_ms = timed(lambda: csm.rollback_context(store, first.context_id, rolled_back_at="2026-07-16T00:03:00Z"))
    check("rollback", rolled.status == csm.RecordStatus.ACTIVE and rollback_ms < 10)

    char_store = character_fixture()
    char_before = cm2.serialize_memory_store(char_store)
    view, interop_ms = timed(lambda: csm.build_character_context_view(char_store, character_ids=("char-1",), token_budget=64, now=T1))
    check("Character Memory interoperability view", len(view) == 1 and cm2.serialize_memory_store(char_store) == char_before)

    check("schema separation", csm.SCHEMA_VERSION == "1.0" and cm2.SCHEMA_VERSION == "2.0")
    check("production boundary", not {"translate", "run_provider", "build_prompt"} & set(csm.__all__))
    print(f"BENCHMARK context_add_ms={add_ms:.3f}")
    print(f"BENCHMARK participant_ops_ms={participant_ms:.3f}")
    print(f"BENCHMARK selection_ms={selection_ms:.3f}")
    print(f"BENCHMARK scene_transition_ms={transition_ms:.3f}")
    print(f"BENCHMARK rollback_ms={rollback_ms:.3f}")
    print(f"BENCHMARK character_interop_view_ms={interop_ms:.3f}")
    print("ALL PASS")


if __name__ == "__main__":
    main()
