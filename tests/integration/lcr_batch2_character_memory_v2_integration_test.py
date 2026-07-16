from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

import core.character_memory_v2 as cm2
from core.character_memory_v2 import (
    AddDisposition,
    ApprovalMetadata,
    ApprovalStatus,
    CharacterMemoryValidationError,
    EvidenceType,
    FactType,
    MemoryStatus,
    MemoryStore,
    add_or_merge_memory,
    approve_memory,
    create_evidence,
    create_memory,
    deserialize_memory_store,
    rollback_memory,
    select_prompt_eligible_memories,
    serialize_memory_store,
)


ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "core" / "character_memory_v2"
T0 = "2026-07-16T00:00:00Z"
T1 = "2026-07-16T00:01:00Z"
T2 = "2026-07-16T00:02:00Z"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ev(kind: str, case: str, segment: str, excerpt: str):
    return create_evidence(
        evidence_type=kind,
        source_case_id=case,
        source_segment_id=segment,
        source_text_hash=digest(case + segment + excerpt),
        excerpt=excerpt,
        language="ko",
        observed_at=T0,
    )


def record(value: str, *, segment: str, kind: str = "source_observation", fact_type: str = "role_or_identity", character_id: str = "char-taeui", confidence: float = 0.95):
    return create_memory(
        character_id=character_id,
        fact_type=fact_type,
        value=value,
        evidence=ev(kind, "case-lcr-2", segment, value),
        confidence=confidence,
        created_at=T0,
    )


def test_end_to_end_offline_governance_selection_serialization_and_rollback():
    store = MemoryStore()
    base = record("已批准人物身分", segment="seg-1")
    add_or_merge_memory(store, base, now=T0)
    approved = approve_memory(store, base.memory_id, approved_at=T1, reviewer="reviewer-1", decision_reference="decision-1")
    inferred = record("推測的性格", segment="seg-2", kind="ai_inference", fact_type="personality_trait", confidence=0.99)
    add_or_merge_memory(store, inferred, now=T1)

    selected = select_prompt_eligible_memories(store, token_budget=256, now=T2)
    assert [item.memory_id for item in selected.items] == [approved.memory_id]
    assert selected.estimated_tokens <= selected.token_budget

    encoded = serialize_memory_store(store)
    restored = deserialize_memory_store(encoded)
    assert serialize_memory_store(restored) == encoded
    rolled = rollback_memory(restored, approved.memory_id, rolled_back_at="2026-07-16T00:03:00Z")
    assert rolled.approval_status == ApprovalStatus.PENDING
    assert len(rolled.evidence) >= 2


def test_conflicting_human_approved_values_are_visible_and_fail_closed():
    store = MemoryStore()
    records = []
    for value, segment in (("鄭泰義", "seg-a"), ("鄭太義", "seg-b")):
        evidence = ev("human_approved", "case-approved", segment, value)
        records.append(create_memory(
            character_id="char-taeui", fact_type="canonical_name", value=value, evidence=evidence,
            confidence=0.9, approval_status="approved",
            approval_metadata=ApprovalMetadata(value, T0, "reviewer", segment), created_at=T0,
        ))
    assert add_or_merge_memory(store, records[0], now=T0).disposition == AddDisposition.ACCEPTED
    result = add_or_merge_memory(store, records[1], now=T1)
    assert result.disposition == AddDisposition.CONFLICT
    assert result.conflict and result.conflict.unresolved
    assert not select_prompt_eligible_memories(store, now=T2).items


def test_tic_batch7_approved_corrections_are_external_references_only():
    index_path = ROOT / "artifacts" / "tic_batch7" / "OFFLINE_QUALITY_GATE_INDEX.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert len(index["items"]) == 2
    store = MemoryStore()
    for item in index["items"]:
        reference = f"external-approved-ref:{item['regression_id']}"
        evidence = create_evidence(
            evidence_type=EvidenceType.HISTORICAL_IMPORT,
            source_case_id=item["case_id"],
            source_segment_id=item["regression_id"],
            source_text_hash=digest(json.dumps(item, ensure_ascii=False, sort_keys=True)),
            excerpt="external approved evidence reference",
            language="ko",
            observed_at=T0,
        )
        imported = create_memory(
            character_id=f"unresolved:tic-{item['regression_id'][-8:]}",
            fact_type=FactType.OTHER,
            value=reference,
            evidence=evidence,
            confidence=0.5,
            created_at=T0,
        )
        add_or_merge_memory(store, imported, now=T0)
    assert len(store.records) == 2
    assert all(item.unresolved_identity for item in store.records.values())
    assert not select_prompt_eligible_memories(store, now=T1).items
    serialized = serialize_memory_store(store)
    fixtures = json.loads((ROOT / "artifacts" / "tic_batch7" / "OFFLINE_QUALITY_GATE_FIXTURES.json").read_text(encoding="utf-8"))
    approved_rows = [item for item in fixtures["items"] if item.get("kind") == "human_approved"]
    assert len(approved_rows) == 2
    assert all(item["source_text"] not in serialized and item["translation_text"] not in serialized for item in approved_rows)


def test_character_memory_package_does_not_import_tic_runtime_provider_prompt_or_network_modules():
    forbidden = (
        "translation_intelligence_corpus", "translation_runtime", "ai_provider", "prompt_builder",
        "prompt_compiler", "requests", "httpx", "urllib", "socket", "openai",
    )
    imports = []
    for path in MODULE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
    assert not [name for name in imports if any(token in name for token in forbidden)]


def test_package_has_no_file_store_or_executable_input_path():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in MODULE_DIR.glob("*.py"))
    assert "pickle" not in combined
    assert "eval(" not in combined
    assert "exec(" not in combined
    assert "write_text(" not in combined
    assert "open(" not in combined


def test_public_api_is_finite_and_has_no_name_inference_or_production_entrypoint():
    required = {
        "create_memory", "add_or_merge_memory", "approve_memory", "reject_memory", "supersede_memory",
        "expire_memory", "rollback_memory", "select_prompt_eligible_memories", "serialize_memory_store",
        "deserialize_memory_store", "validate_memory_store",
    }
    assert required <= set(cm2.__all__)
    forbidden = {"translate", "run_provider", "inject_prompt", "transliterate_name", "auto_complete_name", "extract_character"}
    assert not forbidden & set(cm2.__all__)
    assert len(cm2.__all__) <= 40


def test_snapshot_restore_is_equivalent_and_fail_closed():
    store = MemoryStore()
    original = record("穩定身分", segment="seg-snapshot")
    add_or_merge_memory(store, original, now=T0)
    snapshot = store.snapshot()
    add_or_merge_memory(store, record("另一事實", segment="seg-second", fact_type="other"), now=T1)
    store.restore_snapshot(snapshot)
    assert list(store.records) == [original.memory_id]
    broken = dict(snapshot)
    broken["schema_version"] = "unknown"
    before = serialize_memory_store(store)
    with pytest.raises(CharacterMemoryValidationError):
        store.restore_snapshot(broken)
    assert serialize_memory_store(store) == before


def test_one_hundred_record_selection_is_deterministic_and_bounded():
    store = MemoryStore()
    for index in range(100):
        item = record(f"人物事實 {index}", segment=f"seg-{index}", fact_type="other", character_id=f"char-{index:03d}")
        add_or_merge_memory(store, item, now=T0)
    first = select_prompt_eligible_memories(store, token_budget=256, now=T1)
    second = select_prompt_eligible_memories(store, token_budget=256, now=T1)
    assert first == second
    assert first.estimated_tokens <= 256
    assert len(first.items) < len(store.records)


def test_boundary_declarations_remain_offline():
    boundary = {
        "provider_executed": False,
        "network_requests": 0,
        "new_translation_generated": False,
        "production_integration": False,
        "prompt_integration": False,
        "scene_memory_implemented": False,
        "chunk_cache_v2_implemented": False,
        "dual_pass_implemented": False,
        "multilingual_profiles_implemented": False,
        "lcr_batch3_started": False,
    }
    assert boundary == {
        "provider_executed": False, "network_requests": 0, "new_translation_generated": False,
        "production_integration": False, "prompt_integration": False, "scene_memory_implemented": False,
        "chunk_cache_v2_implemented": False, "dual_pass_implemented": False,
        "multilingual_profiles_implemented": False, "lcr_batch3_started": False,
    }


def test_audit_schema_covers_required_model_and_governance_enums():
    schema = json.loads((ROOT / "audits" / "legacy_capability_recovery" / "batch2" / "LCR_BATCH2_CHARACTER_MEMORY_SCHEMA.json").read_text(encoding="utf-8"))
    memory_schema = schema["$defs"]["memory"]
    required = {
        "memory_id", "character_id", "fact_type", "value", "evidence", "evidence_type", "confidence",
        "approval_status", "source_language", "source_case_id", "source_segment_id", "created_at", "updated_at",
        "version", "expiry_policy", "status",
    }
    assert required <= set(memory_schema["required"])
    assert set(memory_schema["properties"]["fact_type"]["enum"]) == {item.value for item in cm2.FactType}
    assert set(memory_schema["properties"]["status"]["enum"]) == {item.value for item in cm2.MemoryStatus}


def test_frozen_boundary_hash_manifest_recomputes_exactly():
    report = json.loads((ROOT / "audits" / "legacy_capability_recovery" / "batch2" / "LCR_BATCH2_BOUNDARY_REPORT.json").read_text(encoding="utf-8"))
    assert report["status"] == "PASS" and len(report["hash_groups"]) == 11
    for group in report["hash_groups"].values():
        aggregate = hashlib.sha256()
        assert group["file_count"] == len(group["files"]) > 0
        for item in group["files"]:
            actual = hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest()
            assert actual == item["sha256"]
            aggregate.update(item["path"].encode("utf-8") + b"\0" + actual.encode("ascii") + b"\n")
        assert aggregate.hexdigest() == group["aggregate_sha256"]


def test_audit_reports_state_implemented_offline_and_batch3_not_started():
    audit = ROOT / "audits" / "legacy_capability_recovery" / "batch2"
    implementation = json.loads((audit / "LCR_BATCH2_IMPLEMENTATION_REPORT.json").read_text(encoding="utf-8"))
    security = json.loads((audit / "LCR_BATCH2_SECURITY_REPORT.json").read_text(encoding="utf-8"))
    performance = json.loads((audit / "LCR_BATCH2_PERFORMANCE_REPORT.json").read_text(encoding="utf-8"))
    assert implementation["status"] == "implemented_offline" and implementation["next_batch_started"] is False
    assert security["provider_dependency"] is False and security["credential_storage"] is False
    assert performance["status"] == "PASS" and all(performance["threshold_results"].values())
