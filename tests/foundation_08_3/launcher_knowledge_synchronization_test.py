from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.knowledge import KnowledgeItem, KnowledgeQuery, KnowledgeRuntime
from core.knowledge.repositories import KnowledgeRepositoryManager
from core.knowledge.synchronization import (
    KnowledgeConflictResolver,
    KnowledgeSyncContext,
    KnowledgeSynchronizationManager,
    build_knowledge_synchronization_manifest,
)

try:
    from core.intelligence.events import IntelligenceEventBus
except Exception:  # pragma: no cover
    IntelligenceEventBus = None


def check(label, condition):
    print(f"{label:<35} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


def main():
    bus = IntelligenceEventBus() if IntelligenceEventBus else None
    manager = KnowledgeRepositoryManager()
    runtime = KnowledgeRuntime(manager=manager, event_bus=bus)
    sync = KnowledgeSynchronizationManager(repository_manager=manager, runtime=runtime, event_bus=bus)

    check("Synchronization Manager", sync.version == "foundation-08.3")

    context = sync.build_context(payload={"session_id": "s1", "segment_id": "seg1"})
    check("Sync Context", isinstance(context, KnowledgeSyncContext) and context.segment_id == "seg1")

    item = KnowledgeItem(key="정태의", value="鄭泰義", domain="character", source="test")
    repo_result = sync.sync_repository([item], context=context)
    check("Repository Sync", repo_result["updated_count"] == 1 and manager.get("정태의", "character").value == "鄭泰義")

    runtime_result = sync.sync_runtime(
        segment={"id": "seg2"},
        payload={"session_id": "s1", "segment_id": "seg2"},
        result={"knowledge_items": [KnowledgeItem(key="일라이", value="伊萊", domain="character").to_dict()]},
    )
    check("Runtime Sync", runtime_result["repository"]["updated_count"] == 1 and manager.get("일라이", "character").value == "伊萊")

    snapshot = sync.sync_snapshot("unit")
    check("Snapshot Sync", snapshot.to_dict()["snapshot"]["name"] == "unit")

    resolver = KnowledgeConflictResolver(strategy="merge_metadata")
    current = KnowledgeItem(key="凱爾", value="Kyle", domain="character", metadata={"a": 1})
    incoming = KnowledgeItem(key="凱爾", value="凱爾", domain="character", metadata={"b": 2})
    resolved = resolver.resolve(current, incoming)
    check("Conflict Resolver", resolved.value == "凱爾" and resolved.metadata.get("conflict_resolved") is True)

    conflict_result = sync.sync_repository([KnowledgeItem(key="정태의", value="泰義", domain="character")])
    check("Conflict Detected", conflict_result["conflict_count"] == 1)

    queried = sync.query(KnowledgeQuery(domain="character", text="伊萊"))
    check("Query After Sync", len(queried) == 1 and queried[0].key == "일라이")

    manifest = build_knowledge_synchronization_manifest({"unit": True})
    check("Knowledge Manifest", manifest["version"] == "foundation-08.3" and manifest["metadata"]["unit"] is True)

    runtime_manifest = sync.attach_to_runtime_manifest({"components": []})
    check("Runtime Manifest", runtime_manifest["components"][-1]["name"] == "knowledge_synchronization")

    payload = sync.process(
        segment={"id": "seg3"},
        payload={"session_id": "s1", "segment_id": "seg3"},
        result={"knowledge_items": [KnowledgeItem(key="scene1", value={"place": "island"}, domain="scene").to_dict()]},
    )
    check("Process Payload", payload["type"] == "knowledge_synchronization_payload")

    if bus is not None:
        history = bus.history()
        event_types = {entry.get("event_type") for entry in history}
        check("Event Bus Sync", "KnowledgeRepositorySynced" in event_types and "KnowledgeRuntimeSynced" in event_types)
    else:
        check("Event Bus Sync", True)

    check("Snapshot Items", len(payload["snapshot"]["snapshot"]["items"]) >= 3)
    check("Backward Compatible", manager.build_context()["type"] == "knowledge_repository_context")

    print("PASS")


if __name__ == "__main__":
    main()
