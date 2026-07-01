import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.intelligence import (
    IntelligenceMergeStrategy,
    IntelligenceSessionScope,
    IntelligenceSnapshotManager,
    InMemoryIntelligencePersistence,
    SnapshotVersion,
    TranslationIntelligenceEngine,
    TranslationIntelligenceLifecycle,
)


def check(name, condition):
    status = "PASS" if condition else "FAIL"
    print(f"{name:<34} {status}")
    if not condition:
        raise AssertionError(name)


def main():
    print("NTPE Foundation-07.3 Translation Intelligence Lifecycle Test")
    print("=" * 66)

    scope = IntelligenceSessionScope(job_id="job-001", runtime_id="rt-001", session_id="sess-001")
    check("Session Scope", scope.key() == "job-001:rt-001:sess-001")
    child = scope.child_for_segment("seg-001", metadata={"chapter": 1})
    check("Segment Scope", child.key().endswith("seg-001") and child.metadata["chapter"] == 1)

    version = SnapshotVersion(version_id="snap-001")
    bumped = version.bump()
    check("Snapshot Version", bumped.revision == 2 and bumped.parent_version_id == "snap-001")

    manager = IntelligenceSnapshotManager()
    first = manager.create_snapshot({"characters": [{"source_name": "정태의", "target_name": "鄭泰義"}]}, scope=scope, version=version)
    check("Snapshot Created", first["manifest"]["foundation"] == "07.3")
    second = manager.bump_snapshot(first)
    check("Snapshot Bumped", second["manifest"]["version"]["revision"] == 2)

    strategy = IntelligenceMergeStrategy()
    merged = strategy.merge(
        {"glossary": [{"source_term": "일라이", "target_term": "伊萊"}]},
        {"glossary": [{"source_term": "일라이", "target_term": "伊萊・里格勞", "locked": True}]},
    )
    check("Snapshot Merge", len(merged["glossary"]) == 1 and merged["glossary"][0]["locked"] is True)

    persistence = InMemoryIntelligencePersistence()
    saved = persistence.save_snapshot(scope.key(), first)
    loaded = persistence.load_snapshot(scope.key())
    check("Persistence Contract", saved == loaded and scope.key() in persistence.list_scope_keys())

    engine = TranslationIntelligenceEngine()
    engine.characters.remember("정태의", "鄭泰義", aliases=["태의"])
    engine.glossary.remember("일라이 리그로우", "伊萊・里格勞", category="character", locked=True)

    lifecycle = TranslationIntelligenceLifecycle(engine=engine, scope=scope, persistence=persistence)
    check("Lifecycle Created", lifecycle.active_snapshot["manifest"]["scope"]["scope_key"] == scope.key())

    before = lifecycle.before_segment("seg-001", "정태의는 일라이 리그로우를 보았다.")
    check("Lifecycle Before", before["stage"] == "before_segment")
    check("Prompt Context", before["prompt_context"]["type"] == "translation_intelligence_engine_context")

    after = lifecycle.after_segment(
        "seg-001",
        "정태의는 일라이 리그로우를 보았다.",
        "鄭泰義看見了伊萊・里格勞。",
    )
    check("Lifecycle After", after["lifecycle"]["active_scope_key"] == scope.key())
    check("Consistency Passed", after["consistency"]["passed"] is True)

    loaded_segment = lifecycle.load_scope("job-001:rt-001:sess-001:seg-001")
    check("Lifecycle Persisted", loaded_segment is not None and loaded_segment["manifest"]["foundation"] == "07.3")

    external = {"narrative": [{"key": "tone", "value": "緊張", "weight": 4}]}
    merged_active = lifecycle.merge_external_snapshot(external)
    check("External Merge", merged_active["narrative"][0]["key"] == "tone")

    for idx in range(5):
        manager.create_snapshot({"manifest": {"idx": idx}}, scope=scope)
    cleanup = manager.cleanup(keep_last=2)
    check("Lifecycle Cleanup", cleanup["removed"] >= 3 and cleanup["remaining"] == 2)

    exported = lifecycle.cleanup(keep_last=3)
    check("Lifecycle Cleanup Facade", exported["version"] == "foundation-07.3")
    check("Backward Engine", engine.build_snapshot()["manifest"]["foundation"] == "07.1")
    check("Backward Compatible", lifecycle.engine.store is engine.store)

    print("PASS")


if __name__ == "__main__":
    main()
