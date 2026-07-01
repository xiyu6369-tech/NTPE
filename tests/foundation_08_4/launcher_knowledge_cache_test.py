from __future__ import annotations

import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.knowledge import (
    KnowledgeCacheManager,
    KnowledgeCacheRuntime,
    KnowledgeCacheSnapshot,
    KnowledgeCacheStore,
    KnowledgeItem,
    KnowledgeQuery,
    KnowledgeRepositoryManager,
    build_lru_policy,
    build_ttl_policy,
)
from core.knowledge.cache.manifest import build_knowledge_cache_manifest
from core.knowledge.synchronization import KnowledgeSynchronizationManager


class SimpleEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload=None):
        self.events.append((event_type, payload))


def ok(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"{name:<35} PASS")


def seed_manager():
    manager = KnowledgeRepositoryManager()
    manager.ingest_items([
        KnowledgeItem(key="鄭泰義", value="主角", domain="character", source="test"),
        KnowledgeItem(key="伊萊", value="重要角色", domain="character", source="test"),
        KnowledgeItem(key="UNHRDO", value="聯合國人力資源開發組織", domain="glossary", source="test"),
        KnowledgeItem(key="南國島嶼", value="度假場景", domain="scene", source="test"),
        KnowledgeItem(key="關係", value="角色互動狀態", domain="narrative", source="test"),
    ])
    return manager


def main():
    manager = seed_manager()
    bus = SimpleEventBus()
    cache = KnowledgeCacheManager(repository_manager=manager, policy=build_lru_policy(max_size=3), event_bus=bus)

    ok("Cache Manager", cache.version == "foundation-08.4")

    q = KnowledgeQuery(domain="character")
    first = cache.query(q)
    second = cache.query(q)
    ok("Repository Cache", len(first) == 2 and len(second) == 2)
    ok("Cache Hit", cache.metrics()["hits"] >= 1)
    ok("Cache Miss", cache.metrics()["misses"] >= 1)

    character_context = cache.character_context()
    glossary_context = cache.glossary_context()
    narrative_context = cache.narrative_context()
    scene_context = cache.scene_context()
    ok("Character Cache", len(character_context["items"]) == 2)
    ok("Glossary Cache", len(glossary_context["items"]) == 1)
    ok("Narrative Cache", len(narrative_context["items"]) == 1)
    ok("Scene Cache", len(scene_context["items"]) == 1)

    snap = cache.snapshot("knowledge")
    snap_again = cache.snapshot("knowledge")
    ok("Snapshot Cache", len(snap.items) == len(snap_again.items) == 5)

    cache.put_item(KnowledgeItem(key="新角色", value="新增", domain="character", source="test"))
    after = cache.query(KnowledgeQuery(domain="character"))
    ok("Cache Invalidate", len(after) == 3 and cache.metrics()["invalidations"] >= 1)

    lru = KnowledgeCacheStore(policy=build_lru_policy(max_size=2))
    lru.set("a", 1)
    lru.set("b", 2)
    lru.get("a")
    lru.set("c", 3)
    ok("Policy LRU", "b" not in lru.keys() and "a" in lru.keys() and "c" in lru.keys())

    ttl = KnowledgeCacheStore(policy=build_ttl_policy(ttl_seconds=0.01, max_size=5))
    ttl.set("x", 1)
    time.sleep(0.02)
    ok("Policy TTL", ttl.get("x") is None)

    runtime = KnowledgeCacheRuntime(cache_manager=cache)
    payload = runtime.process_segment(
        segment={"id": "seg-1", "text": "鄭泰義前往南國島嶼"},
        payload={"segment_id": "seg-1"},
        prompt_package={},
        result={"knowledge_items": [{"key": "片段記憶", "value": "完成", "domain": "narrative"}]},
        query=KnowledgeQuery(domain="character"),
    )
    ok("Runtime Cache", payload["type"] == "knowledge_cache_runtime_payload")
    ok("Prompt Cache Context", any(c.get("type") == "knowledge_cache_context" for c in payload["prompt_package"].get("context_components", [])))

    sync = KnowledgeSynchronizationManager(repository_manager=manager, event_bus=bus)
    sync_result = sync.sync_repository([KnowledgeItem(key="同步術語", value="sync", domain="glossary")])
    invalidated = cache.handle_sync_result(sync_result)
    ok("Synchronization Invalidate", invalidated >= 0 and cache.query(KnowledgeQuery(domain="glossary")))

    snapshot_helper = KnowledgeCacheSnapshot(cache)
    cache_snapshot = snapshot_helper.build("cache-state")
    restored = snapshot_helper.restore_entries(cache_snapshot)
    ok("Cache Snapshot", cache_snapshot["type"] == "knowledge_cache_snapshot" and restored >= 1)

    manifest = build_knowledge_cache_manifest()
    runtime_manifest = cache.attach_to_runtime_manifest({"components": []})
    ok("Manifest Cache", manifest["version"] == "foundation-08.4")
    ok("Runtime Manifest", runtime_manifest["components"][-1]["name"] == "knowledge_cache")

    ok("Cache Metrics", "hit_rate" in cache.metrics())
    ok("Event Bus Cache", any(event[0] in {"KnowledgeCacheHit", "KnowledgeCacheMiss", "KnowledgeCacheInvalidated"} for event in bus.events))

    # Ensure 08.0/08.1 repository APIs are still directly usable.
    direct = manager.query(KnowledgeQuery(text="鄭泰義"))
    ok("Backward Compatible", len(direct) >= 1)

    print("PASS")


if __name__ == "__main__":
    main()
