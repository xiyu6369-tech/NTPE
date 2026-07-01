import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.knowledge import (
    KnowledgeAPI,
    KnowledgeCacheManager,
    KnowledgeFilter,
    KnowledgeItem,
    KnowledgePagination,
    KnowledgeQuery,
    KnowledgeQueryBuilder,
    KnowledgeQueryExecutor,
    KnowledgeRepositoryManager,
    KnowledgeSort,
    build_knowledge_api_manifest,
)


class EventBus:
    def __init__(self):
        self.events = []
    def publish(self, event_type, payload=None):
        self.events.append((event_type, payload))


def check(name, condition):
    print(f"{name:<35} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def build_api():
    manager = KnowledgeRepositoryManager()
    manager.ingest_items([
        KnowledgeItem(key="鄭泰義", value="主角", domain="character", metadata={"rank": 2}),
        KnowledgeItem(key="伊萊", value="重要角色", domain="character", metadata={"rank": 1}),
        KnowledgeItem(key="UNHRDO", value="組織", domain="glossary", metadata={"rank": 3}),
        KnowledgeItem(key="南國島嶼", value="度假場景", domain="scene", metadata={"rank": 4}),
        KnowledgeItem(key="關係變化", value="敘事狀態", domain="narrative", metadata={"rank": 5}),
    ])
    bus = EventBus()
    cache = KnowledgeCacheManager(repository_manager=manager, event_bus=bus)
    return KnowledgeAPI(manager=manager, cache_manager=cache, event_bus=bus), bus


def main():
    api, bus = build_api()

    result = api.query(KnowledgeQuery(domain="character"))
    check("Knowledge API", len(result.items) == 2)

    request = api.builder().domain("character").text("伊萊").limit(1).build()
    check("Query Builder", request.query.domain == "character" and request.query.text == "伊萊")

    executor = KnowledgeQueryExecutor(manager=api.manager, cache_manager=api.cache_manager)
    executed = executor.execute(request)
    check("Query Executor", len(executed.items) == 1 and executed.items[0].key == "伊萊")

    filtered = KnowledgeFilter(domain="character", metadata={"rank": 2}).apply(api.manager.query(KnowledgeQuery()))
    check("Filter Query", len(filtered) == 1 and filtered[0].key == "鄭泰義")

    sorted_items = KnowledgeSort(field="rank", reverse=True).apply(api.manager.query(KnowledgeQuery()))
    check("Sort Query", sorted_items[0].key == "關係變化")

    page, meta = KnowledgePagination(offset=1, limit=2).apply(api.manager.query(KnowledgeQuery()))
    check("Pagination", len(page) == 2 and meta["total"] == 5 and meta["has_more"] is True)

    runtime_payload = api.runtime_query(segment={"id": "seg-1"}, domain="character")
    check("Runtime Query", runtime_payload["type"] == "knowledge_runtime_query" and runtime_payload["segment_id"] == "seg-1")

    prompt_package = api.prompt_query({"context_components": []}, domain="glossary")
    check("Prompt Query", len(prompt_package["context_components"]) == 1)

    plugin_payload = api.plugin_query("quality_plugin", KnowledgeQuery(domain="scene"))
    check("Plugin Query", plugin_payload["plugin"] == "quality_plugin" and len(plugin_payload["result"]["items"]) == 1)

    api.cache_query(KnowledgeQuery(domain="character"))
    cache_payload = api.cache_query(KnowledgeQuery(domain="character"))
    check("Cache Query", cache_payload["cache_metrics"].get("hits", 0) >= 1)

    snapshot = api.snapshot_query("api-test")
    check("Snapshot Query", snapshot["name"] == "api-test" and len(snapshot["items"]) >= 5)

    got = api.get("鄭泰義", "character")
    check("Get Query", got is not None and got.value == "主角")

    search = api.search("組織", limit=1)
    check("Search Query", len(search) == 1 and search[0].domain == "glossary")

    manifest = api.manifest()
    check("Knowledge Manifest", manifest["version"] == "foundation-08.5" and "query_api" in manifest["capabilities"])

    runtime_manifest = api.attach_to_runtime_manifest({"components": []})
    check("Runtime Manifest", runtime_manifest["components"][-1]["name"] == "knowledge_query_api")

    api.put("新角色", "測試", domain="character")
    check("Put Invalidates Cache", api.get("新角色", "character") is not None)

    check("Event Bus Query", any(event[0] == "KnowledgeQueryExecuted" for event in bus.events))

    # 08.0-08.4 compatibility smoke checks.
    check("Backward Compatible", hasattr(api.manager, "snapshot") and hasattr(api.cache_manager, "metrics"))

    print("PASS")


if __name__ == "__main__":
    main()
