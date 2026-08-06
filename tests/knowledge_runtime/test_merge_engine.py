from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.knowledge_runtime import (
    DOMAIN_STRATEGIES,
    KnowledgeBundle,
    KnowledgeEntry,
    KnowledgeLoadError,
    KnowledgeLoader,
    KnowledgeManagerError,
    KnowledgeMerger,
    KnowledgePrototype,
    KnowledgeResolveError,
    KnowledgeResolver,
    KnowledgeRuntimeError,
    KnowledgeRuntimeManager,
    KnowledgeSnapshot,
    KnowledgeSnapshotError,
    KnowledgeSnapshotStore,
    MergedKnowledge,
    MergedRuntime,
    MergeStrategy,
    SnapshotHierarchy,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<55} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


# ============================================================
# MergedKnowledge & MergedRuntime model tests
# ============================================================

def test_merged_knowledge_model() -> None:
    mk = MergedKnowledge(
        domain="character",
        entries={"정태의": "鄭泰義", "리차드": "理查"},
        strategy=MergeStrategy.KEY_OVERRIDE,
    )
    check("MergedKnowledge domain", mk.domain == "character")
    check("MergedKnowledge entry count", mk.entry_count == 2)
    check("MergedKnowledge strategy", mk.strategy == MergeStrategy.KEY_OVERRIDE)

    d = mk.to_dict()
    restored = MergedKnowledge.from_dict(d)
    check("MergedKnowledge roundtrip", restored.domain == "character" and restored.entry_count == 2)

    print("merged_knowledge_model PASS")


def test_merged_runtime_model() -> None:
    mr = MergedRuntime(
        domains={
            "character": MergedKnowledge(domain="character", entries={"A": "a"}, strategy=MergeStrategy.KEY_OVERRIDE),
            "glossary": MergedKnowledge(domain="glossary", entries={"B": "b"}, strategy=MergeStrategy.KEY_OVERRIDE),
        }
    )
    check("MergedRuntime domain count", mr.domain_count == 2)
    check("MergedRuntime total entries", mr.total_entries == 2)
    check("MergedRuntime get_domain", mr.get_domain("character").entry_count == 1)
    check("MergedRuntime resolve", mr.resolve("A", "character") == "a")
    check("MergedRuntime resolve missing", mr.resolve("X", "character") is None)
    check("MergedRuntime resolve_all", mr.resolve_all("character") == {"A": "a"})

    d = mr.to_dict()
    restored = MergedRuntime.from_dict(d)
    check("MergedRuntime roundtrip", restored.domain_count == 2 and restored.total_entries == 2)

    print("merged_runtime_model PASS")


# ============================================================
# Merge Strategy tests
# ============================================================

def test_domain_strategies() -> None:
    check("Character strategy KEY_OVERRIDE", DOMAIN_STRATEGIES["character"] == MergeStrategy.KEY_OVERRIDE)
    check("Glossary strategy KEY_OVERRIDE", DOMAIN_STRATEGIES["glossary"] == MergeStrategy.KEY_OVERRIDE)
    check("Scene strategy REPLACE", DOMAIN_STRATEGIES["scene"] == MergeStrategy.REPLACE)
    check("Narrative strategy REPLACE", DOMAIN_STRATEGIES["narrative"] == MergeStrategy.REPLACE)
    check("Style strategy REPLACE", DOMAIN_STRATEGIES["style"] == MergeStrategy.REPLACE)

    print("domain_strategies PASS")


# ============================================================
# Character merge tests (KEY_OVERRIDE)
# ============================================================

def test_character_merge_novel_only() -> None:
    merger = KnowledgeMerger()
    merger.set_novel("character", {"정태의": "鄭泰義 (novel)", "리차드": "理查 (novel)"})
    merged = merger.merge_domain("character")

    check("Character novel only - 정태의", merged.entries["정태의"] == "鄭泰義 (novel)")
    check("Character novel only - 리차드", merged.entries["리차드"] == "理查 (novel)")
    check("Character novel only - strategy", merged.strategy == MergeStrategy.KEY_OVERRIDE)

    print("character_merge_novel_only PASS")


def test_character_merge_novel_chapter() -> None:
    merger = KnowledgeMerger()
    merger.set_novel("character", {"정태의": "鄭泰義 (novel)", "리차드": "理查 (novel)", "영웅": "주인공 (novel)"})
    merger.set_chapter("character", {"정태의": "鄭泰義 (chapter)", "악당": "반역자 (chapter)"})
    merged = merger.merge_domain("character")

    check("Character novel+chapter - 정태의 (chapter overrides)", merged.entries["정태의"] == "鄭泰義 (chapter)")
    check("Character novel+chapter - 리차드 (novel preserved)", merged.entries["리차드"] == "理查 (novel)")
    check("Character novel+chapter - 영웅 (novel preserved)", merged.entries["영웅"] == "주인공 (novel)")
    check("Character novel+chapter - 악당 (new from chapter)", merged.entries["악당"] == "반역자 (chapter)")
    check("Character novel+chapter - entry count", merged.entry_count == 4)

    print("character_merge_novel_chapter PASS")


def test_character_merge_chunk_override() -> None:
    merger = KnowledgeMerger()
    merger.set_novel("character", {"정태의": "鄭泰義 (novel)"})
    merger.set_volume("character", {"정태의": "鄭泰義 (volume)"})
    merger.set_chapter("character", {"정태의": "鄭泰義 (chapter)"})
    merger.set_chunk("character", {"정태의": "鄭泰義 (chunk)", "신캐릭터": "새로운캐릭터 (chunk)"})
    merged = merger.merge_domain("character")

    check("Character chunk override - 정태의", merged.entries["정태의"] == "鄭泰義 (chunk)")
    check("Character chunk override - 신캐릭터", merged.entries["신캐릭터"] == "새로운캐릭터 (chunk)")
    check("Character chunk override - entry count", merged.entry_count == 2)

    print("character_merge_chunk_override PASS")


# ============================================================
# Glossary merge tests (KEY_OVERRIDE)
# ============================================================

def test_glossary_merge_duplicate_keys() -> None:
    merger = KnowledgeMerger()
    merger.set_novel("glossary", {"UNHRDO": "국제기구 (novel)", "AI": "인공지능 (novel)"})
    merger.set_chapter("glossary", {"UNHRDO": "유엔기구 (chapter)", "ML": "머신러닝 (chapter)"})
    merged = merger.merge_domain("glossary")

    check("Glossary duplicate - UNHRDO overridden", merged.entries["UNHRDO"] == "유엔기구 (chapter)")
    check("Glossary duplicate - AI preserved", merged.entries["AI"] == "인공지능 (novel)")
    check("Glossary duplicate - ML new", merged.entries["ML"] == "머신러닝 (chapter)")
    check("Glossary duplicate - entry count", merged.entry_count == 3)

    print("glossary_merge_duplicate_keys PASS")


def test_glossary_merge_new_keys() -> None:
    merger = KnowledgeMerger()
    merger.set_novel("glossary", {"TERM1": "용어1"})
    merger.set_volume("glossary", {"TERM2": "용어2"})
    merger.set_chapter("glossary", {"TERM3": "용어3"})
    merger.set_chunk("glossary", {"TERM4": "용어4"})
    merged = merger.merge_domain("glossary")

    check("Glossary new keys - all present", merged.entry_count == 4)
    check("Glossary new keys - TERM1", merged.entries["TERM1"] == "용어1")
    check("Glossary new keys - TERM4", merged.entries["TERM4"] == "용어4")

    print("glossary_merge_new_keys PASS")


# ============================================================
# Replace strategy domain tests (Scene, Narrative, Style)
# ============================================================

def test_scene_merge_replace() -> None:
    merger = KnowledgeMerger()
    merger.set_novel("scene", {"scene_1": "장소1 (novel)", "scene_2": "장소2 (novel)"})
    merger.set_chapter("scene", {"scene_3": "장소3 (chapter)"})
    merged = merger.merge_domain("scene")

    # REPLACE strategy: only lowest non-empty level (chapter) wins
    check("Scene replace - only chapter entries", merged.entry_count == 1)
    check("Scene replace - scene_3", merged.entries["scene_3"] == "장소3 (chapter)")
    check("Scene replace - novel entries gone", "scene_1" not in merged.entries)

    print("scene_merge_replace PASS")


def test_narrative_merge_replace() -> None:
    merger = KnowledgeMerger()
    merger.set_novel("narrative", {"intro": "이야기 시작 (novel)", "middle": "중간 (novel)"})
    merger.set_volume("narrative", {"ending": "결말 (volume)"})
    merged = merger.merge_domain("narrative")

    # REPLACE: only volume (lowest non-empty) wins
    check("Narrative replace - only volume", merged.entry_count == 1)
    check("Narrative replace - ending", merged.entries["ending"] == "결말 (volume)")

    print("narrative_merge_replace PASS")


def test_style_merge_replace() -> None:
    merger = KnowledgeMerger()
    merger.set_novel("style", {"tone": "formal (novel)"})
    merger.set_chunk("style", {"tone": "casual (chunk)", "voice": "active (chunk)"})
    merged = merger.merge_domain("style")

    # REPLACE: only chunk (lowest non-empty) wins
    check("Style replace - only chunk", merged.entry_count == 2)
    check("Style replace - tone from chunk", merged.entries["tone"] == "casual (chunk)")
    check("Style replace - voice from chunk", merged.entries["voice"] == "active (chunk)")

    print("style_merge_replace PASS")


# ============================================================
# Snapshot Hierarchy merge order tests
# ============================================================

def test_snapshot_hierarchy_merge_order() -> None:
    merger = KnowledgeMerger()

    # Novel level
    merger.set_novel("character", {"A": "a-novel", "B": "b-novel", "C": "c-novel"})
    # Volume level
    merger.set_volume("character", {"B": "b-volume", "D": "d-volume"})
    # Chapter level
    merger.set_chapter("character", {"C": "c-chapter", "E": "e-chapter"})
    # Chunk level (highest priority)
    merger.set_chunk("character", {"C": "c-chunk", "F": "f-chunk"})

    merged = merger.merge_domain("character")

    # KEY_OVERRIDE: each level overrides specific keys
    check("Hierarchy A from novel", merged.entries["A"] == "a-novel")
    check("Hierarchy B from volume", merged.entries["B"] == "b-volume")
    check("Hierarchy C from chunk (overrides chapter)", merged.entries["C"] == "c-chunk")
    check("Hierarchy D from volume", merged.entries["D"] == "d-volume")
    check("Hierarchy E from chapter", merged.entries["E"] == "e-chapter")
    check("Hierarchy F from chunk", merged.entries["F"] == "f-chunk")
    check("Hierarchy total entries", merged.entry_count == 6)

    print("snapshot_hierarchy_merge_order PASS")


def test_snapshot_hierarchy_cross_domain_priority() -> None:
    merger = KnowledgeMerger()

    merger.set_novel("character", {"주인공": "메인 (novel)"})
    merger.set_novel("glossary", {"용어": "정의 (novel)"})
    merger.set_chapter("character", {"주인공": "챕터주인공 (chapter)"})
    merger.set_chunk("glossary", {"용어": "청크정의 (chunk)"})

    char_merged = merger.merge_domain("character")
    glossary_merged = merger.merge_domain("glossary")

    check("Cross-domain character priority", char_merged.entries["주인공"] == "챕터주인공 (chapter)")
    check("Cross-domain glossary priority", glossary_merged.entries["용어"] == "청크정의 (chunk)")

    print("snapshot_hierarchy_cross_domain_priority PASS")


# ============================================================
# Resolver tests (must query merged runtime only)
# ============================================================

def test_resolver_from_merged_runtime() -> None:
    merged = MergedRuntime(
        domains={
            "character": MergedKnowledge(
                domain="character",
                entries={"정태의": "鄭泰義 (merged)", "리차드": "理查 (merged)"},
                strategy=MergeStrategy.KEY_OVERRIDE,
            ),
            "glossary": MergedKnowledge(
                domain="glossary",
                entries={"UNHRDO": "유엔기구 (merged)"},
                strategy=MergeStrategy.KEY_OVERRIDE,
            ),
        }
    )

    resolver = KnowledgeResolver().load_from_merged_runtime(merged)

    check("Resolver from merged - character count", len(resolver.resolve_domain("character")) == 2)
    check("Resolver from merged - 정태의", resolver.resolve_character("정태의").value == "鄭泰義 (merged)")
    check("Resolver from merged - UNHRDO", resolver.resolve_term("UNHRDO").value == "유엔기구 (merged)")

    # Verify resolver only sees merged data
    check("Resolver domain keys from merged", set(resolver.domain_keys) == {"character", "glossary"})

    print("resolver_from_merged_runtime PASS")


def test_resolver_merged_only_never_raw_snapshots() -> None:
    """Verify resolver never inspects raw snapshots directly."""
    merger = KnowledgeMerger()
    merger.set_novel("character", {"A": "a-novel"})
    merger.set_chunk("character", {"A": "a-chunk", "B": "b-chunk"})
    merged = merger.merge_all()

    resolver = KnowledgeResolver().load_from_merged_runtime(merged)

    # Resolver should only see merged result (chunk level wins for KEY_OVERRIDE)
    entries = resolver.resolve_domain("character")
    check("Resolver sees only merged - A from chunk", any(e.key == "A" and e.value == "a-chunk" for e in entries))
    check("Resolver sees only merged - B from chunk", any(e.key == "B" and e.value == "b-chunk" for e in entries))
    check("Resolver does not see novel A", not any(e.key == "A" and e.value == "a-novel" for e in entries))

    print("resolver_merged_only_never_raw_snapshots PASS")


# ============================================================
# Empty merge tests
# ============================================================

def test_empty_merge_no_crash() -> None:
    merger = KnowledgeMerger()
    merged = merger.merge_all()

    check("Empty merge - no crash", merged.domain_count == 0)
    check("Empty merge - total entries 0", merged.total_entries == 0)
    check("Empty merge - get_domain returns None", merged.get_domain("character") is None)
    check("Empty merge - resolve returns None", merged.resolve("any", "character") is None)
    check("Empty merge - resolve_all returns {}", merged.resolve_all("character") == {})

    print("empty_merge_no_crash PASS")


def test_merge_domain_missing_graceful() -> None:
    merger = KnowledgeMerger()
    merger.set_novel("character", {"A": "a"})

    # Merge a domain that has no entries
    merged = merger.merge_domain("glossary")

    check("Missing domain - empty entries", merged.entry_count == 0)
    check("Missing domain - strategy default", merged.strategy == MergeStrategy.KEY_OVERRIDE)
    check("Missing domain - domain name preserved", merged.domain == "glossary")

    print("merge_domain_missing_graceful PASS")


# ============================================================
# Manager integration tests
# ============================================================

def test_manager_build_merged_runtime() -> None:
    source = {
        "character": {"주인공": {"value": "메인캐릭터"}},
        "glossary": {"용어": {"value": "정의"}},
    }
    manager = KnowledgeRuntimeManager(source)

    bundles = manager.load_all()
    merged = manager.build_merged_runtime(bundles=list(bundles.values()))

    check("Manager build merged - domains", merged.domain_count == 2)
    check("Manager build merged - character", merged.get_domain("character").entry_count == 1)
    check("Manager build merged - glossary", merged.get_domain("glossary").entry_count == 1)

    print("manager_build_merged_runtime PASS")


def test_manager_resolve_merged() -> None:
    source = {
        "character": {"주인공": {"value": "메인캐릭터"}},
        "glossary": {"용어": {"value": "정의"}},
    }
    manager = KnowledgeRuntimeManager(source)
    bundles = manager.load_all()
    manager.build_merged_runtime(bundles=list(bundles.values()))

    entry = manager.resolve_merged("주인공", "character")
    check("Manager resolve_merged", entry.value == "메인캐릭터" and entry.source == "merged_runtime")

    entries = manager.resolve_all_merged("character")
    check("Manager resolve_all_merged", len(entries) == 1 and entries[0].key == "주인공")

    print("manager_resolve_merged PASS")


def test_manager_resolve_merged_requires_built() -> None:
    manager = KnowledgeRuntimeManager({})
    try:
        _ = manager.resolve_merged("A", "character")
        check("Manager resolve_merged requires built", False)
    except KnowledgeManagerError:
        check("Manager resolve_merged requires built", True)

    print("manager_resolve_merged_requires_built PASS")


def test_manager_merge_snapshots() -> None:
    source = {
        "character": {"A": {"value": "a"}},
    }
    manager = KnowledgeRuntimeManager(source)
    bundle = manager.load_character()
    snapshot = manager.snapshots.build("snap-1", bundles=[bundle])

    merged = manager.build_merged_runtime(snapshots=[snapshot])

    check("Manager merge snapshots - domain", merged.get_domain("character").entry_count == 1)
    check("Manager merge snapshots - value", merged.resolve("A", "character") == "a")

    print("manager_merge_snapshots PASS")


def test_manager_manifest_includes_merger() -> None:
    manager = KnowledgeRuntimeManager({})
    manifest = manager.manifest()

    check("Manager manifest has merger", "merger" in manifest)
    check("Manager manifest merger name", manifest["merger"]["name"] == "knowledge_merger")
    check("Manager manifest version", manifest["version"] == "rm-6.1.2")

    print("manager_manifest_includes_merger PASS")


# ============================================================
# Merger manifest test
# ============================================================

def test_merger_manifest() -> None:
    merger = KnowledgeMerger()
    merger.set_novel("character", {"A": "a"})
    merger.set_chunk("character", {"B": "b"})

    manifest = merger.manifest()
    check("Merger manifest name", manifest["name"] == "knowledge_merger")
    check("Merger manifest version", manifest["version"] == "rm-6.1.2")
    check("Merger manifest hierarchy populated", "character" in manifest["hierarchy"]["populated_layers"]["novel"])
    check("Merger manifest hierarchy chunk", "character" in manifest["hierarchy"]["populated_layers"]["chunk"])

    merged = merger.merge_all()
    manifest2 = merger.manifest()
    check("Merger manifest has merged runtime", manifest2["has_merged_runtime"] is True)

    print("merger_manifest PASS")


# ============================================================
# Main
# ============================================================

def main() -> None:
    test_merged_knowledge_model()
    test_merged_runtime_model()
    test_domain_strategies()
    test_character_merge_novel_only()
    test_character_merge_novel_chapter()
    test_character_merge_chunk_override()
    test_glossary_merge_duplicate_keys()
    test_glossary_merge_new_keys()
    test_scene_merge_replace()
    test_narrative_merge_replace()
    test_style_merge_replace()
    test_snapshot_hierarchy_merge_order()
    test_snapshot_hierarchy_cross_domain_priority()
    test_resolver_from_merged_runtime()
    test_resolver_merged_only_never_raw_snapshots()
    test_empty_merge_no_crash()
    test_merge_domain_missing_graceful()
    test_manager_build_merged_runtime()
    test_manager_resolve_merged()
    test_manager_resolve_merged_requires_built()
    test_manager_merge_snapshots()
    test_manager_manifest_includes_merger()
    test_merger_manifest()
    print("ALL MERGE ENGINE TESTS PASS")


if __name__ == "__main__":
    main()