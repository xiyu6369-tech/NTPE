"""Foundation-08.1 adapter from Foundation-07 intelligence snapshots."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..repositories.memory_repository import KnowledgeMemoryRepository


class IntelligenceKnowledgeAdapter:
    """Convert intelligence snapshots into repository items."""

    def __init__(self, repository: Optional[KnowledgeMemoryRepository] = None):
        self.repository = repository or KnowledgeMemoryRepository(metadata={"adapter": "intelligence"})

    def ingest_snapshot(self, snapshot: Optional[Dict[str, Any]]) -> KnowledgeMemoryRepository:
        snapshot = snapshot or {}
        for key, value in dict(snapshot.get("characters") or {}).items():
            self.repository.put_value(str(key), value, domain="character", source="intelligence")
        for key, value in dict(snapshot.get("glossary") or {}).items():
            self.repository.put_value(str(key), value, domain="glossary", source="intelligence")

        narrative = snapshot.get("narrative") or []
        iterable = narrative.items() if isinstance(narrative, dict) else enumerate(narrative)
        for key, value in iterable:
            self.repository.put_value(str(key), value, domain="narrative", source="intelligence")

        scenes = snapshot.get("scenes") or []
        scene_iterable = scenes.items() if isinstance(scenes, dict) else enumerate(scenes)
        for key, value in scene_iterable:
            self.repository.put_value(str(key), value, domain="scene", source="intelligence")
        return self.repository

    def export_snapshot(self) -> Dict[str, Any]:
        snapshot = self.repository.snapshot("intelligence_adapter").to_dict()
        snapshot["adapter"] = "intelligence"
        return snapshot


__all__ = ["IntelligenceKnowledgeAdapter"]
