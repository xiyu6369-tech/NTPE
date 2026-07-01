import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.knowledge import (
    KnowledgeCacheManager,
    KnowledgeIndexBuilder,
    KnowledgeItem,
    KnowledgeQuery,
    KnowledgeRepositoryManager,
    KnowledgeSemanticIndex,
    KnowledgeSemanticSearchEngine,
    KnowledgeTokenizer,
    build_knowledge_semantic_manifest,
)


RESULTS = []


def check(name, condition):
    status = "PASS" if condition else "FAIL"
    RESULTS.append((name, status))
    print(f"{name:<35} {status}")
    if not condition:
        raise AssertionError(name)


def seed_manager():
    manager = KnowledgeRepositoryManager()
    manager.ingest_items([
        KnowledgeItem(key="jeong-taeui", value="鄭泰義 是主要角色，陽光健氣，適應力強。", domain="character", metadata={"alias": "정태의"}),
        KnowledgeItem(key="ilay-rigrow", value="伊萊・里格勞 是危險且強勢的角色。", domain="character", metadata={"alias": "일라이"}),
        KnowledgeItem(key="UNHRDO", value="聯合國人力資源開發機構，重要組織術語。", domain="glossary", metadata={"type": "organization"}),
        KnowledgeItem(key="island-vacation", value="南國島嶼度假場景，包含海邊與飯店。", domain="scene", metadata={"place": "island"}),
        KnowledgeItem(key="relationship-tension", value="角色關係目前存在緊張與佔有慾。", domain="narrative", metadata={"kind": "relationship"}),
    ])
    return manager


def main():
    manager = seed_manager()
    tokenizer = KnowledgeTokenizer()
    tokens = tokenizer.tokenize("鄭泰義 character island vacation")
    check("Tokenizer", "鄭泰義" in tokens and "character" in tokens)

    index = KnowledgeSemanticIndex()
    index.build(manager.snapshot("seed").items)
    check("Semantic Index", index.manifest()["metadata"]["document_count"] == 5)

    builder = KnowledgeIndexBuilder(manager)
    built = builder.from_repository()
    check("Index Builder", built.manifest()["metadata"]["document_count"] == 5)

    search_results = built.search("鄭泰義", limit=3)
    check("Search Engine", len(search_results) >= 1 and search_results[0].item.key == "jeong-taeui")

    ranked_scores = [result.score for result in built.search("角色", domain="character")]
    check("Ranking", ranked_scores == sorted(ranked_scores, reverse=True))

    hybrid_engine = KnowledgeSemanticSearchEngine(manager=manager, index=built)
    hybrid = hybrid_engine.hybrid_search("南國 島嶼", limit=2)
    check("Hybrid Search", len(hybrid) >= 1 and hybrid[0].item.domain == "scene")

    runtime_payload = hybrid_engine.runtime_semantic_query({"id": "seg-001"}, text="伊萊 危險", domain="character", limit=2)
    check("Runtime Semantic", runtime_payload["type"] == "knowledge_runtime_semantic_query" and runtime_payload["segment_id"] == "seg-001")

    prompt_package = hybrid_engine.prompt_semantic_context({"context_components": []}, text="組織 術語", domain="glossary", limit=2)
    check("Prompt Semantic", prompt_package["context_components"][-1]["type"] == "knowledge_semantic_context")

    cache_manager = KnowledgeCacheManager(repository_manager=manager)
    cached_engine = KnowledgeSemanticSearchEngine(manager=manager, cache_manager=cache_manager)
    cache_payload = cached_engine.cache_semantic_query("角色", domain="character", limit=2)
    check("Cache Semantic", "cache_metrics" in cache_payload and len(cache_payload["results"]) >= 1)

    manifest = build_knowledge_semantic_manifest({"test": True})
    check("Manifest Semantic", manifest["version"] == "foundation-08.6" and "hybrid_search" in manifest["capabilities"])

    runtime_manifest = cached_engine.attach_to_runtime_manifest({"components": []})
    check("Runtime Manifest", runtime_manifest["components"][-1]["name"] == "knowledge_semantic_index")

    serialized = built.to_dict()
    restored = KnowledgeSemanticIndex.from_dict(serialized)
    check("Index Serializable", restored.manifest()["metadata"]["document_count"] == built.manifest()["metadata"]["document_count"])

    query_items = restored.query(KnowledgeQuery(text="UNHRDO", domain="glossary", limit=1))
    check("Query Compatible", len(query_items) == 1 and query_items[0].key == "UNHRDO")

    # Existing repository/cache/API layers should remain importable and usable.
    cache_manager.character_context()
    check("Backward Compatible", cache_manager.metrics()["size"] >= 1)

    print("PASS")


if __name__ == "__main__":
    main()
