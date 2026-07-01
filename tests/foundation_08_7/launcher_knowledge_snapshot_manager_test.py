import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.knowledge import (
    InMemoryKnowledgeRepository,
    KnowledgeItem,
    KnowledgeQuery,
    KnowledgeSnapshot,
    KnowledgeSnapshotDiffer,
    KnowledgeSnapshotManager,
    KnowledgeSnapshotRegistry,
    KnowledgeSnapshotSerializer,
    build_knowledge_snapshot_manifest,
    build_snapshot_manager,
    merge_snapshots,
)


def report(name, ok):
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise AssertionError(name)


class EventBusStub:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload=None):
        self.events.append((event_type, payload or {}))


def main():
    repo = InMemoryKnowledgeRepository(metadata={"test": "08.7"})
    repo.put(KnowledgeItem(key="Jeong Taeui", value="鄭泰義", domain="character", metadata={"role": "lead"}))
    repo.put(KnowledgeItem(key="Ilay", value="伊萊", domain="character"))
    repo.put(KnowledgeItem(key="UNHRDO", value="聯合國人類資源開發機構", domain="glossary"))

    bus = EventBusStub()
    manager = KnowledgeSnapshotManager(repository=repo, event_bus=bus)

    snapshot_a = manager.create("chapter-001", label="initial")
    report("Snapshot Manager", isinstance(snapshot_a, KnowledgeSnapshot) and snapshot_a.version == "foundation-08.7")

    registry = KnowledgeSnapshotRegistry()
    registry.register(snapshot_a)
    report("Snapshot Registry", registry.get("chapter-001") is snapshot_a and "chapter-001" in registry.list())

    report("Snapshot History", manager.history.latest().revision == 1 and len(manager.history.list()) == 1)

    repo.put(KnowledgeItem(key="Kyle", value="凱爾", domain="character"))
    repo.delete("UNHRDO", "glossary")
    snapshot_b = manager.create("chapter-002", label="updated")

    differ = KnowledgeSnapshotDiffer()
    diff = differ.diff(snapshot_a, snapshot_b)
    report("Snapshot Diff", len(diff.added) == 1 and len(diff.removed) == 1 and diff.has_changes())

    merged = manager.merge("merged", ["chapter-001", "chapter-002"])
    report("Snapshot Merge", merged.name == "merged" and len(merged.items) == 4)

    repo.put(KnowledgeItem(key="Temp", value="暫存", domain="scene"))
    manager.rollback(name="chapter-001")
    report("Snapshot Rollback", repo.get("Temp", "scene") is None and repo.get("UNHRDO", "glossary") is not None)

    serializer = KnowledgeSnapshotSerializer()
    encoded = serializer.dumps(snapshot_a)
    decoded = serializer.loads(encoded)
    report("Snapshot Serializer", decoded.name == snapshot_a.name and len(decoded.items) == len(snapshot_a.items))

    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, "snapshot.json")
        manager.export("chapter-001", path)
        imported = manager.import_snapshot(path, name="imported")
        report("Snapshot Export", os.path.exists(path))
        report("Snapshot Import", imported.name == "imported" and "imported" in manager.list())

    runtime_payload = manager.snapshot_runtime_payload("runtime")
    report("Runtime Snapshot", "knowledge_snapshot" in runtime_payload and "knowledge_snapshot_manifest" in runtime_payload)

    manifest = manager.attach_runtime_manifest({"runtime": "demo"}, name="runtime-manifest")
    report("Runtime Manifest", manifest.get("knowledge_snapshot_manager", {}).get("version") == "foundation-08.7")

    report("Event Bus Snapshot", any(event[0] == "KnowledgeSnapshotCreated" for event in bus.events))

    public_manifest = build_knowledge_snapshot_manifest(extra="ok")
    report("Manifest Snapshot", "snapshot_rollback" in public_manifest["capabilities"] and public_manifest["metadata"]["extra"] == "ok")

    direct_merged = merge_snapshots("direct", [snapshot_a, snapshot_b], prefer="first")
    report("Snapshot Merge Helper", direct_merged.name == "direct" and direct_merged.metadata["prefer"] == "first")

    built = build_snapshot_manager(repository=repo, source="helper")
    report("Manager Helper", built.manifest()["metadata"]["source"] == "helper")

    remaining = repo.query(KnowledgeQuery(domain="character"))
    report("Query Compatible", len(remaining) >= 2)

    report("Backward Compatible", repo.get("Jeong Taeui", "character").value == "鄭泰義")
    print("PASS")


if __name__ == "__main__":
    main()
