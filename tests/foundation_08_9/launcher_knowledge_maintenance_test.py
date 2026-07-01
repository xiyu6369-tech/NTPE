import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.knowledge import (
    KnowledgeCacheManager,
    KnowledgeItem,
    KnowledgeMaintenanceManager,
    KnowledgeMemoryRepository,
    KnowledgeQuery,
    KnowledgeRepositoryManager,
    KnowledgeSnapshotManager,
    build_knowledge_maintenance_manifest,
)


def check(name, condition):
    print(f"{name:<35} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def build_manager():
    repo = KnowledgeMemoryRepository()
    repo.put(KnowledgeItem(key="taeui", value="鄭泰義", domain="character"))
    repo.put(KnowledgeItem(key="ilay", value="伊萊", domain="character"))
    repo.put(KnowledgeItem(key="UNHRDO", value="聯合國人力資源開發機構", domain="glossary"))
    repo.put(KnowledgeItem(key="scene-1", value={"place": "island"}, domain="scene"))
    return KnowledgeRepositoryManager(repository=repo)


def main():
    repository_manager = build_manager()
    maintenance = KnowledgeMaintenanceManager(repository_manager=repository_manager)

    # Repository cleanup should be safe and no-op on clean repositories.
    cleanup_result = maintenance.repository_cleanup()
    check("Repository Cleanup", cleanup_result["remaining_count"] >= 4)

    optimize_result = maintenance.repository_optimize()
    check("Repository Optimize", optimize_result["optimized"] and optimize_result["item_count"] >= 4)

    rebuild_result = maintenance.repository_rebuild(repository_manager.snapshot("rebuild"))
    check("Repository Rebuild", rebuild_result["rebuilt"] and rebuild_result["item_count"] >= 4)

    cache_manager = KnowledgeCacheManager(repository_manager=repository_manager)
    cache_manager.query(KnowledgeQuery(domain="character"))
    cache_result = maintenance.cache_cleanup(cache_manager)
    check("Cache Cleanup", cache_result["enabled"] and cache_result["removed_count"] >= 1)

    cache_rebuild = maintenance.cache_rebuild(cache_manager)
    check("Cache Rebuild", cache_rebuild["rebuilt"] and "character" in cache_rebuild["warmed_domains"])

    snapshot_manager = KnowledgeSnapshotManager(repository=repository_manager.repository)
    snapshot_manager.create("s1")
    snapshot_manager.create("s2")
    snapshot_manager.create("s3")
    snapshot_cleanup = maintenance.snapshot_cleanup(snapshot_manager, keep_latest=1)
    check("Snapshot Cleanup", snapshot_cleanup["enabled"] and snapshot_cleanup["remaining_count"] == 1)

    snapshot_manager.create("s4")
    compact = maintenance.snapshot_compact(snapshot_manager, keep_latest=1)
    check("Snapshot Compaction", compact["compacted"])

    integrity = maintenance.integrity_check()
    check("Integrity Check", integrity["valid"] is True)

    diagnostics = maintenance.diagnostics_report(cache_manager=cache_manager, snapshot_manager=snapshot_manager)
    check("Diagnostics", diagnostics["diagnostics"]["repository_available"] is True)

    health = maintenance.health_report(cache_manager=cache_manager, snapshot_manager=snapshot_manager)
    check("Health Report", health["healthy"] is True)

    repair_engine = maintenance.repair_engine()
    check("Repair Engine", repair_engine.version == "foundation-08.9")

    duplicates = maintenance.duplicate_detection()
    check("Duplicate Detection", duplicates["duplicate_count"] == 0)

    # Broken references should be removed without deleting valid items.
    item = repository_manager.get("scene-1", "scene")
    item.metadata["references"] = ["taeui", "missing-ref"]
    repository_manager.repository.put(item)
    repair_result = maintenance.auto_repair()
    repaired_item = repository_manager.get("scene-1", "scene")
    check("Broken Reference Repair", "missing-ref" not in repaired_item.metadata.get("references", []))

    stats = maintenance.statistics_report(cache_manager=cache_manager, snapshot_manager=snapshot_manager)
    check("Statistics", stats["repository"]["item_count"] >= 4)

    manifest = maintenance.manifest()
    check("Manifest Maintenance", manifest["version"] == "foundation-08.9")

    runtime_manifest = maintenance.attach_to_runtime_manifest({"components": []})
    check("Runtime Manifest", any(c.get("name") == "knowledge_maintenance" for c in runtime_manifest["components"]))

    helper_manifest = build_knowledge_maintenance_manifest({"stage": "test"})
    check("Manifest Helper", helper_manifest["metadata"]["stage"] == "test")

    # Existing query/repository behavior must remain unchanged.
    results = repository_manager.query(KnowledgeQuery(text="鄭泰義"))
    check("Query Compatible", len(results) == 1 and results[0].key == "taeui")

    snapshot = repository_manager.snapshot("backward")
    check("Backward Compatible", snapshot.name == "backward" and len(snapshot.items) >= 4)

    print("PASS")


if __name__ == "__main__":
    main()
