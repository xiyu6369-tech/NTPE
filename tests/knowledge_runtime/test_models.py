from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.knowledge_runtime import (
    KnowledgeBundle,
    KnowledgeEntry,
    KnowledgeLoadError,
    KnowledgeLoader,
    KnowledgeManagerError,
    KnowledgePrototype,
    KnowledgeResolveError,
    KnowledgeResolver,
    KnowledgeRuntimeError,
    KnowledgeRuntimeManager,
    KnowledgeSnapshot,
    KnowledgeSnapshotError,
    KnowledgeSnapshotStore,
    SnapshotHierarchy,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<40} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


SOURCE = {
    "character": {
        "정태의": {"value": "鄭泰義", "kind": "name"},
        "리차드": {"value": "理查", "kind": "name"},
    },
    "glossary": {
        "UNHRDO": {"value": "聯合國人力資源開發組織", "kind": "org"},
    },
    "narrative": [
        {"key": "stage_intro", "metadata": {"value": "主角抵達教育中心", "chapter": 1}},
    ],
    "scene": {
        "scene_001": {"value": "UNHRDO 總部大廳", "kind": "location"},
    },
    "style": {
        "translator_policy": {"value": "保留原文風格", "kind": "global"},
    },
}


def test_models() -> None:
    entry = KnowledgeEntry(key="정태의", value="鄭泰義", domain="character")
    check("Entry frozen struct", entry.key == "정태의")
    check("Entry to_dict roundtrip", entry.to_dict()["key"] == "정태의")
    restored = KnowledgeEntry.from_dict(entry.to_dict())
    check("Entry from_dict roundtrip", restored.key == entry.key and restored.value == entry.value)

    bundle = KnowledgeBundle(id="bundle-1", entries=[entry], domain="character")
    check("Bundle entry count", bundle.entry_count == 1)
    check("Bundle to_dict", bundle.to_dict()["entry_count"] == 1)
    restored_bundle = KnowledgeBundle.from_dict(bundle.to_dict())
    check("Bundle from_dict roundtrip", restored_bundle.id == "bundle-1" and restored_bundle.entry_count == 1)

    snapshot = KnowledgeSnapshot(id="snap-1", bundles=[bundle])
    check("Snapshot bundle count", snapshot.bundle_count == 1)
    check("Snapshot entry count", snapshot.entry_count == 1)
    check("Snapshot to_dict", snapshot.to_dict()["bundle_count"] == 1)
    restored_snapshot = KnowledgeSnapshot.from_dict(snapshot.to_dict())
    check("Snapshot from_dict roundtrip", restored_snapshot.id == "snap-1" and restored_snapshot.entry_count == 1)

    proto = KnowledgePrototype(key="test", domain="character")
    check("Prototype immutable key", proto.key == "test")
    check("Prototype version", proto.version == "rm-6.1.0")

    print("models PASS")


def test_loader() -> None:
    loader = KnowledgeLoader(SOURCE)
    all_domains = loader.load_all()
    check("Loader all domains", set(all_domains.keys()) == {"character", "glossary", "narrative", "scene", "style"})

    chars = loader.load_domain("character")
    check("Loader character count", len(chars) == 2)
    check("Loader character keys", {c.key for c in chars} == {"정태의", "리차드"})

    filtered = loader.load_keys("character", ["정태의"])
    check("Loader filter keys", len(filtered) == 1 and filtered[0].key == "정태의")

    manifest = loader.manifest()
    check("Loader manifest version", manifest["version"] == "rm-6.1.1")

    try:
        _ = loader.load_domain("nonexistent")
        check("Loader missing domain raises", False)
    except KnowledgeLoadError:
        check("Loader missing domain raises", True)

    print("loader PASS")


def test_loader_domain_bundles() -> None:
    loader = KnowledgeLoader(SOURCE)

    char_bundle = loader.load_character_bundle({"stage": "rm-6.1"})
    check("Character bundle id", char_bundle.id == "bundle-character")
    check("Character bundle domain", char_bundle.domain == "character")
    check("Character bundle count", char_bundle.entry_count == 2)
    check("Character bundle metadata", char_bundle.metadata.get("stage") == "rm-6.1")

    glossary_bundle = loader.load_glossary_bundle()
    check("Glossary bundle id", glossary_bundle.id == "bundle-glossary")
    check("Glossary bundle count", glossary_bundle.entry_count == 1)
    check("Glossary bundle entry key", glossary_bundle.entries[0].key == "UNHRDO")

    scene_bundle = loader.load_scene_bundle()
    check("Scene bundle id", scene_bundle.id == "bundle-scene")
    check("Scene bundle count", scene_bundle.entry_count == 1)

    narrative_bundle = loader.load_narrative_bundle()
    check("Narrative bundle id", narrative_bundle.id == "bundle-narrative")
    check("Narrative bundle count", narrative_bundle.entry_count == 1)

    style_bundle = loader.load_style_bundle()
    check("Style bundle id", style_bundle.id == "bundle-style")
    check("Style bundle count", style_bundle.entry_count == 1)
    check("Style bundle entry key", style_bundle.entries[0].key == "translator_policy")

    all_bundles = loader.load_all_bundles()
    check("Load all bundles count", len(all_bundles) == 5)
    check(
        "Load all bundles domains",
        set(all_bundles.keys()) == {"character", "glossary", "scene", "narrative", "style"},
    )

    print("loader_domain_bundles PASS")


def test_loader_missing_domain_graceful() -> None:
    partial_source = {"character": {"정태의": {"value": "鄭泰義"}}}
    loader = KnowledgeLoader(partial_source)

    all_bundles = loader.load_all_bundles()
    check("Partial load all bundles count", len(all_bundles) == 1)
    check("Partial load only character", "character" in all_bundles)
    check("Partial load no glossary", "glossary" not in all_bundles)

    try:
        _ = loader.load_glossary_bundle()
        check("Missing glossary raises", False)
    except KnowledgeLoadError:
        check("Missing glossary raises", True)

    print("loader_missing_domain PASS")


def test_resolver() -> None:
    prototypes = [
        KnowledgePrototype(key="정태의", domain="character", metadata={"value": "鄭泰義"}),
        KnowledgePrototype(key="UNHRDO", domain="glossary", metadata={"value": "聯合國人力資源開發組織"}),
    ]
    resolver = KnowledgeResolver(prototypes)
    resolver.index_prototypes()

    entry = resolver.resolve("정태의", "character")
    check("Resolver resolve", entry.value == "鄭泰義")

    all_entries = resolver.resolve_all()
    check("Resolver all count", len(all_entries) == 2)

    chars = resolver.resolve_domain("character")
    check("Resolver char count", len(chars) == 1 and chars[0].key == "정태의")

    check("Resolver domain keys", resolver.domain_keys == ["character", "glossary"])

    found = resolver.find_prototype("UNHRDO", "glossary")
    check("Resolver find", found is not None and found.key == "UNHRDO")

    missing = resolver.find_prototype("unknown", "general")
    check("Resolver find missing", missing is None)

    try:
        _ = resolver.resolve("unknown", "general")
        check("Resolver raises on missing", False)
    except KnowledgeResolveError:
        check("Resolver raises on missing", True)

    manifest = resolver.manifest()
    check("Resolver manifest name", manifest["name"] == "knowledge_resolver")

    empty_result = KnowledgeResolver().resolve_all()
    check("Resolver empty resolve", len(empty_result) == 0)

    print("resolver PASS")


def test_resolver_domain_lookup() -> None:
    prototypes = [
        KnowledgePrototype(key="정태의", domain="character", metadata={"value": "鄭泰義"}),
        KnowledgePrototype(key="리차드", domain="character", metadata={"value": "理查"}),
        KnowledgePrototype(key="UNHRDO", domain="glossary", metadata={"value": "聯合國人力資源開發組織"}),
        KnowledgePrototype(key="scene_001", domain="scene", metadata={"value": "大廳"}),
        KnowledgePrototype(key="intro", domain="narrative", metadata={"value": "故事開始"}),
        KnowledgePrototype(key="tone", domain="style", metadata={"value": "formal"}),
    ]
    resolver = KnowledgeResolver(prototypes)
    resolver.index_prototypes()

    char_entry = resolver.resolve_character("정태의")
    check("Resolve character", char_entry.value == "鄭泰義")

    term_entry = resolver.resolve_term("UNHRDO")
    check("Resolve term", term_entry.value == "聯合國人力資源開發組織")

    scene_entry = resolver.resolve_scene("scene_001")
    check("Resolve scene", scene_entry.value == "大廳")

    narrative_entry = resolver.resolve_narrative()
    check("Resolve narrative", narrative_entry.value == "故事開始")

    style_entry = resolver.resolve_style()
    check("Resolve style", style_entry.value == "formal")

    try:
        _ = resolver.resolve_character("unknown")
        check("Resolve missing character raises", False)
    except KnowledgeResolveError:
        check("Resolve missing character raises", True)

    try:
        _ = resolver.resolve_term("unknown_term")
        check("Resolve missing term raises", False)
    except KnowledgeResolveError:
        check("Resolve missing term raises", True)

    print("resolver_domain_lookup PASS")


def test_resolver_missing_narrative_style() -> None:
    prototypes = [
        KnowledgePrototype(key="a", domain="character", metadata={"value": "A"}),
    ]
    resolver = KnowledgeResolver(prototypes)
    resolver.index_prototypes()

    try:
        _ = resolver.resolve_narrative()
        check("Resolve missing narrative raises", False)
    except KnowledgeResolveError:
        check("Resolve missing narrative raises", True)

    try:
        _ = resolver.resolve_style()
        check("Resolve missing style raises", False)
    except KnowledgeResolveError:
        check("Resolve missing style raises", True)

    print("resolver_missing_narrative_style PASS")


def test_snapshot_store() -> None:
    store = KnowledgeSnapshotStore()

    entry = KnowledgeEntry(key="정태의", value="鄭泰義", domain="character")
    bundle = KnowledgeBundle(id="bundle-1", entries=[entry], domain="character")
    snapshot = store.build("snap-1", bundles=[bundle])
    check("Snapshot build", snapshot.id == "snap-1")

    retrieved = store.retrieve("snap-1")
    check("Snapshot retrieve", retrieved.entry_count == 1)

    entries = store.restore_entries("snap-1")
    check("Snapshot restore entries", len(entries) == 1 and entries[0].key == "정태의")

    bundles = store.restore_bundles("snap-1")
    check("Snapshot restore bundles", len(bundles) == 1 and bundles[0].id == "bundle-1")

    check("Snapshot list has id", "snap-1" in store.list_ids())

    store.delete("snap-1")
    check("Snapshot deleted", "snap-1" not in store.list_ids())

    try:
        _ = store.retrieve("snap-1")
        check("Snapshot error after delete", False)
    except KnowledgeSnapshotError:
        check("Snapshot error after delete", True)

    store.build("snap-2", metadata={"stage": "rm-6.1"})
    snap2 = store.retrieve("snap-2")
    check("Snapshot metadata", snap2.metadata.get("stage") == "rm-6.1")

    manifest = store.manifest()
    check("Snapshot manifest version", manifest["version"] == "rm-6.1.1")

    print("snapshot PASS")


def test_snapshot_hierarchy() -> None:
    hierarchy = SnapshotHierarchy()

    hierarchy.set_novel("character", {"정태의": "鄭泰義 (global)", "英雄": "主角 (global)"})
    hierarchy.set_volume("character", {"정태의": "鄭泰義 (vol2)"})
    hierarchy.set_chapter("character", {"英雄": "男主角 (ch3)"})
    hierarchy.set_chunk("character", {"정태의": "鄭泰義 (ch3-chunk5)"})

    char = hierarchy.resolve("정태의", "character")
    check("Hierarchy chunk overrides all", char == "鄭泰義 (ch3-chunk5)")

    hero = hierarchy.resolve("英雄", "character")
    check("Hierarchy chapter overrides novel", hero == "男主角 (ch3)")

    missing = hierarchy.resolve("없는_키", "character")
    check("Hierarchy missing key None", missing is None)

    all_chars = hierarchy.resolve_all("character")
    check("Hierarchy merged count", len(all_chars) == 2)
    check("Hierarchy merged 英雄", all_chars["英雄"] == "男主角 (ch3)")
    check("Hierarchy merged 정태의", all_chars["정태의"] == "鄭泰義 (ch3-chunk5)")

    manifest = hierarchy.manifest()
    check("Hierarchy manifest name", manifest["name"] == "snapshot_hierarchy")
    check("Hierarchy manifest levels", manifest["levels"] == ["novel", "volume", "chapter", "chunk"])

    print("snapshot_hierarchy PASS")


def test_snapshot_hierarchy_cross_domain() -> None:
    hierarchy = SnapshotHierarchy()

    hierarchy.set_novel("glossary", {"UNHRDO": "聯合國 (novel)"})
    hierarchy.set_chapter("glossary", {"UNHRDO": "聯合國人資開發組織 (ch3)"})

    value = hierarchy.resolve("UNHRDO", "glossary")
    check("Hierarchy cross-domain chapter overrides novel", value == "聯合國人資開發組織 (ch3)")

    merged = hierarchy.resolve_all("glossary")
    check("Hierarchy cross-domain merged", merged["UNHRDO"] == "聯合國人資開發組織 (ch3)")

    print("snapshot_hierarchy_cross_domain PASS")


def test_snapshot_hierarchy_invalid_level() -> None:
    hierarchy = SnapshotHierarchy()
    try:
        hierarchy.set_layer("invalid", "character", {})
        check("Hierarchy invalid level raises", False)
    except KnowledgeSnapshotError:
        check("Hierarchy invalid level raises", True)

    print("snapshot_hierarchy_invalid_level PASS")


def test_manager() -> None:
    manager = KnowledgeRuntimeManager(SOURCE)

    entries = manager.load_and_resolve("character")
    check("Manager load/resolve", len(entries) == 2)

    bundle = manager.build_bundle("bundle-c", "character", {"stage": "rm-6.1"})
    check("Manager build bundle", bundle.entry_count == 2 and bundle.metadata.get("stage") == "rm-6.1")

    store_bundle_ref = manager.snapshots.build("bundle-snap", [bundle])
    captured = manager.capture("cap-1", bundle_ids=["bundle-snap"])
    check("Manager capture", captured.id == "cap-1" and captured.entry_count == 2)

    restored = manager.restore("cap-1")
    check("Manager restore", len(restored) == 2 and restored[0].key == "정태의")

    manifest = manager.manifest()
    check("Manager manifest version", manifest["version"] == "rm-6.1.1")
    check("Manager manifest loader", manifest["loader"]["name"] == "knowledge_loader")
    check("Manager manifest resolver", manifest["resolver"]["name"] == "knowledge_resolver")
    check("Manager manifest snapshots", manifest["snapshots"]["name"] == "knowledge_snapshot_store")

    print("manager PASS")


def test_manager_domain_load() -> None:
    manager = KnowledgeRuntimeManager(SOURCE)

    char_bundle = manager.load_character()
    check("Manager load_character", char_bundle.domain == "character" and char_bundle.entry_count == 2)

    glossary_bundle = manager.load_glossary()
    check("Manager load_glossary", glossary_bundle.domain == "glossary" and glossary_bundle.entry_count == 1)

    scene_bundle = manager.load_scene()
    check("Manager load_scene", scene_bundle.domain == "scene" and scene_bundle.entry_count == 1)

    narrative_bundle = manager.load_narrative()
    check("Manager load_narrative", narrative_bundle.domain == "narrative" and narrative_bundle.entry_count == 1)

    style_bundle = manager.load_style()
    check("Manager load_style", style_bundle.domain == "style" and style_bundle.entry_count == 1)

    all_bundles = manager.load_all()
    check("Manager load_all count", len(all_bundles) == 5)

    print("manager_domain_load PASS")


def test_errors() -> None:
    base = KnowledgeRuntimeError("base")
    load_err = KnowledgeLoadError("load")
    resolve_err = KnowledgeResolveError("resolve")
    snap_err = KnowledgeSnapshotError("snap")
    mgr_err = KnowledgeManagerError("mgr")

    check("Error base str", str(base) == "base")
    check("Error load str", str(load_err) == "load")
    check("Error load inheritance", isinstance(load_err, KnowledgeRuntimeError))
    check("Error resolve inheritance", isinstance(resolve_err, KnowledgeRuntimeError))
    check("Error snapshot inheritance", isinstance(snap_err, KnowledgeRuntimeError))
    check("Error manager inheritance", isinstance(mgr_err, KnowledgeRuntimeError))

    print("errors PASS")


def main() -> None:
    test_models()
    test_loader()
    test_loader_domain_bundles()
    test_loader_missing_domain_graceful()
    test_resolver()
    test_resolver_domain_lookup()
    test_resolver_missing_narrative_style()
    test_snapshot_store()
    test_snapshot_hierarchy()
    test_snapshot_hierarchy_cross_domain()
    test_snapshot_hierarchy_invalid_level()
    test_manager()
    test_manager_domain_load()
    test_errors()
    print("ALL TESTS PASS")


if __name__ == "__main__":
    main()