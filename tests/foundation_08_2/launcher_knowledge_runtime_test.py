from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.knowledge import (
    CharacterKnowledgeProvider,
    GlossaryKnowledgeProvider,
    KnowledgeItem,
    KnowledgeQuery,
    KnowledgeRepositoryManager,
    KnowledgeRuntime,
    KnowledgeContextRuntime,
    KnowledgePromptRuntime,
    KnowledgeRepositoryRuntime,
    KnowledgeSessionRuntime,
    build_knowledge_runtime_manifest,
    build_memory_repository,
)


class LocalEventBus:
    def __init__(self):
        self.events = []

    def publish(self, name, payload=None):
        self.events.append((name, payload))


def check(name: str, condition: bool) -> None:
    print(f"{name:<35} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


def main() -> None:
    manager = KnowledgeRepositoryManager(build_memory_repository(stage="08.2"))
    manager.register_provider("character", CharacterKnowledgeProvider({"정태의": "鄭泰義"}))
    manager.register_provider("glossary", GlossaryKnowledgeProvider({"UNHRDO": "聯合國人力資源開發組織"}))

    context_runtime = KnowledgeContextRuntime(manager)
    context = context_runtime.build_context(segment={"id": "seg-1"}, query=KnowledgeQuery(domain="character"))
    check("Knowledge Runtime", context["type"] == "knowledge_runtime_context")
    check("Context Runtime", context["domains"]["character"]["정태의"] == "鄭泰義")

    prompt_runtime = KnowledgePromptRuntime(context_runtime)
    prompt = prompt_runtime.attach({"context_components": []}, segment={"id": "seg-1"})
    check("Prompt Runtime", prompt["context_components"][-1]["type"] == "knowledge_runtime_context")

    repository_runtime = KnowledgeRepositoryRuntime(manager)
    before = repository_runtime.before_segment(segment={"id": "seg-2"}, payload={"segment_id": "seg-2"})
    check("Repository Runtime", before["knowledge_context"]["segment_id"] == "seg-2")

    result = repository_runtime.after_segment(
        segment={"id": "seg-2"},
        result={"knowledge_items": [KnowledgeItem(key="카일", value="凱爾", domain="character").to_dict()]},
    )
    check("Runtime Snapshot", result["snapshot"]["items"] and manager.get("카일", "character").value == "凱爾")

    session_runtime = KnowledgeSessionRuntime("session-1", manager)
    snapshot = session_runtime.checkpoint("unit")
    restored = KnowledgeSessionRuntime("session-2").restore(snapshot)
    check("Session Runtime", restored.manager.get("정태의", "character").value == "鄭泰義")

    manifest = build_knowledge_runtime_manifest({"unit": True})
    check("Manifest Runtime", manifest["version"] == "foundation-08.2")

    event_bus = LocalEventBus()
    runtime = KnowledgeRuntime(manager=manager, event_bus=event_bus, session_id="runtime-session")
    payload = runtime.process_segment(
        segment={"id": "seg-3"},
        payload={"segment_id": "seg-3"},
        prompt_package={"context_components": []},
        result={"knowledge_items": [KnowledgeItem(key="리차드", value="理查", domain="character").to_dict()]},
    )
    check("Event Bus Runtime", len(event_bus.events) >= 2)
    check("Knowledge Payload", payload["type"] == "knowledge_runtime_payload")
    check("Prompt Package Runtime", payload["prompt_package"]["knowledge_runtime"]["attached"] is True)
    check("Repository Updated", manager.get("리차드", "character").value == "理查")

    runtime_manifest = runtime.attach_to_runtime_manifest({"components": []})
    check("Runtime Manifest", runtime_manifest["components"][-1]["name"] == "knowledge_runtime")
    check("Session Checkpoint", payload["after"]["session"]["history_count"] >= 1)
    check("Backward Compatible", manager.get("정태의", "character").value == "鄭泰義")

    print("PASS")


if __name__ == "__main__":
    main()
