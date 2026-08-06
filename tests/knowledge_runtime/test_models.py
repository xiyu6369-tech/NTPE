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
    check("Loader all domains", set(all_domains.keys()) == {"character", "glossary", "narrative"})

    chars = loader.load_domain("character")
    check("Loader character count", len(chars) == 2)
    check("Loader character keys", {c.key for c in chars} == {"정태의", "리차드"})

    filtered = loader.load_keys("character", ["정태의"])
    check("Loader filter keys", len(filtered) == 1 and filtered[0].key == "정태의")

    manifest = loader.manifest()
    check("Loader manifest version", manifest["version"] == "rm-6.1.0")

    try:
        _ = loader.load_domain("nonexistent")
        check("Loader missing domain", False)
    except KnowledgeLoadError:
        check("Loader missing domain raises", True)

    print("loader PASS")


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
    check("Snapshot manifest version", manifest["version"] == "rm-6.1.0")

    print("snapshot PASS")


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
    check("Manager manifest version", manifest["version"] == "rm-6.1.0")
    check("Manager manifest loader", manifest["loader"]["name"] == "knowledge_loader")
    check("Manager manifest resolver", manifest["resolver"]["name"] == "knowledge_resolver")
    check("Manager manifest snapshots", manifest["snapshots"]["name"] == "knowledge_snapshot_store")

    print("manager PASS")


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
    test_resolver()
    test_snapshot_store()
    test_manager()
    test_errors()
    print("ALL TESTS PASS")


if __name__ == "__main__":
    main()