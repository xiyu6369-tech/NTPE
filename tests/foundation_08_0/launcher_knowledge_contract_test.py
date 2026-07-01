from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.knowledge import (
    InMemoryKnowledgeRepository,
    KnowledgeItem,
    KnowledgeQuery,
    KnowledgeSnapshot,
    RepositoryKnowledgeProvider,
    build_knowledge_manifest,
    build_query,
    build_repository_from_intelligence_snapshot,
    get_default_knowledge_registry,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<35} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    repo = InMemoryKnowledgeRepository()
    repo.put_value("정태의", "鄭泰義", domain="character", metadata={"kind": "name"})
    repo.put_value("UNHRDO", "聯合國人力資源開發組織", domain="glossary")

    check("Knowledge Repository", repo.get("정태의", "character").value == "鄭泰義")

    query = KnowledgeQuery(text="정태의", domain="character")
    check("Knowledge Query", len(repo.query(query)) == 1)

    helper_query = build_query(domain="character", kind="name")
    check("Knowledge Query Helper", len(repo.query(helper_query)) == 1)

    provider = RepositoryKnowledgeProvider(repo)
    context = provider.build_context()
    check("Knowledge Provider", context["domains"]["character"]["정태의"] == "鄭泰義")

    snapshot = repo.snapshot("unit")
    payload = snapshot.to_dict()
    restored = KnowledgeSnapshot.from_dict(payload)
    check("Knowledge Snapshot", restored.items[0].key in {"정태의", "UNHRDO"})

    restored_repo = InMemoryKnowledgeRepository().load_snapshot(restored)
    check("Snapshot Restore", restored_repo.get("UNHRDO", "glossary").value == "聯合國人力資源開發組織")

    registry = get_default_knowledge_registry()
    registry.register("unit", repo, default=True)
    check("Knowledge Registry", registry.get().get("정태의", "character").value == "鄭泰義")
    check("Registry List", "unit" in registry.list())

    manifest = build_knowledge_manifest(stage="contract")
    check("Knowledge Manifest", manifest.to_dict()["version"] == "foundation-08.0")

    runtime_manifest = provider.attach_to_runtime_manifest({"components": []})
    check("Runtime Attached", runtime_manifest["components"][-1]["name"] == "knowledge_layer_contract")

    prompt_package = provider.attach_to_prompt_package({"context_components": []})
    check("Prompt Package Attached", prompt_package["context_components"][-1]["type"] == "knowledge_context")

    intelligence_snapshot = {
        "characters": {"일라이": "伊萊"},
        "glossary": {"계급": "階級"},
        "narrative": ["主角抵達島上"],
        "scenes": [{"location": "南國島嶼"}],
    }
    intelligence_repo = build_repository_from_intelligence_snapshot(intelligence_snapshot)
    check("Intelligence Attached", intelligence_repo.get("일라이", "character").value == "伊萊")
    check("Persistence Compatible", intelligence_repo.snapshot().to_dict()["version"] == "foundation-08.0")

    deleted = repo.delete("UNHRDO", "glossary")
    check("Knowledge Delete", deleted and repo.get("UNHRDO", "glossary") is None)

    item = KnowledgeItem.from_dict(KnowledgeItem("scene", "current", domain="scene").to_dict())
    check("Backward Compatible", item.domain == "scene")

    print("PASS")


if __name__ == "__main__":
    main()
