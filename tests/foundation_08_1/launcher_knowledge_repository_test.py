from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.knowledge import (
    CharacterKnowledgeProvider,
    GlossaryKnowledgeProvider,
    IntelligenceKnowledgeAdapter,
    KnowledgeMemoryRepository,
    KnowledgeQuery,
    KnowledgeRepositoryManager,
    NarrativeKnowledgeProvider,
    PersistenceKnowledgeAdapter,
    RuntimeKnowledgeProvider,
    SceneKnowledgeProvider,
    build_memory_repository,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<35} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    repo = KnowledgeMemoryRepository()
    repo.put_value("정태의", "鄭泰義", domain="character", metadata={"kind": "name"})
    check("Memory Repository", repo.get("정태의", "character").value == "鄭泰義")

    repo.put_many([
        repo.put_value("일라이", "伊萊", domain="character"),
        repo.put_value("UNHRDO", "聯合國人力資源開發組織", domain="glossary"),
    ])
    check("Repository Put Many", repo.get("UNHRDO", "glossary").value == "聯合國人力資源開發組織")
    check("Repository Query Values", "伊萊" in repo.query_values(KnowledgeQuery(domain="character")))

    context = repo.to_context(KnowledgeQuery(domain="character"))
    check("Repository Context", context["domains"]["character"]["정태의"] == "鄭泰義")

    character_provider = CharacterKnowledgeProvider({"카일": "凱爾"})
    glossary_provider = GlossaryKnowledgeProvider({"계급": "階級"})
    narrative_provider = NarrativeKnowledgeProvider(["主角抵達南國島嶼"])
    scene_provider = SceneKnowledgeProvider([{"location": "南國島嶼"}])

    check("Character Provider", character_provider.provide(KnowledgeQuery(domain="character"))[0].value == "凱爾")
    check("Glossary Provider", glossary_provider.provide(KnowledgeQuery(text="계급"))[0].value == "階級")
    check("Narrative Provider", narrative_provider.provide(KnowledgeQuery(domain="narrative"))[0].value == "主角抵達南國島嶼")
    check("Scene Provider", scene_provider.provide(KnowledgeQuery(domain="scene"))[0].value["location"] == "南國島嶼")

    manager = KnowledgeRepositoryManager(build_memory_repository(stage="08.1"))
    manager.register_provider("character", character_provider)
    manager.register_provider("glossary", glossary_provider)
    manager.register_provider("narrative", narrative_provider)
    manager.register_provider("scene", scene_provider)

    check("Manager Registered", sorted(manager.providers.keys()) == ["character", "glossary", "narrative", "scene"])
    check("Manager Ingested", manager.get("카일", "character").value == "凱爾")
    check("Manager Query", manager.query(KnowledgeQuery(domain="glossary"))[0].key == "계급")

    runtime_provider = RuntimeKnowledgeProvider(manager.repository)
    runtime_payload = runtime_provider.attach_to_runtime_payload({"segment_id": "s1"})
    check("Runtime Provider", runtime_payload["knowledge"]["domains"]["character"]["카일"] == "凱爾")

    prompt_package = manager.attach_to_prompt_package({"context_components": []})
    check("Prompt Package", prompt_package["context_components"][-1]["type"] == "knowledge_repository_context")

    runtime_manifest = manager.attach_to_runtime_manifest({"components": []})
    check("Runtime Manifest", runtime_manifest["components"][-1]["name"] == "knowledge_repository")

    snapshot = manager.snapshot("unit")
    restored_manager = KnowledgeRepositoryManager().restore(snapshot)
    check("Repository Snapshot", restored_manager.get("카일", "character").value == "凱爾")

    persistence = PersistenceKnowledgeAdapter()
    persistence.load(snapshot)
    dumped = persistence.dump()
    check("Persistence Adapter", dumped["items"][0]["domain"] in {"character", "glossary", "narrative", "scene"})

    intelligence = IntelligenceKnowledgeAdapter()
    intelligence.ingest_snapshot({
        "characters": {"리차드": "理查"},
        "glossary": {"군부": "軍部"},
        "narrative": ["敘事記憶"],
        "scenes": [{"place": "基地"}],
    })
    check("Intelligence Adapter", intelligence.repository.get("리차드", "character").value == "理查")
    check("Adapter Export", intelligence.export_snapshot()["adapter"] == "intelligence")

    check("Manifest Version", repo.manifest().version == "foundation-08.1")
    check("Backward Compatible", repo.get("정태의", "character").value == "鄭泰義")

    print("PASS")


if __name__ == "__main__":
    main()
