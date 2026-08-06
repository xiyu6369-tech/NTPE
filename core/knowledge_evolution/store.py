"""RM-7.0 Knowledge Evolution Foundation — JSON file-based store.

Organizes knowledge into three tiers:
  knowledge/user/         — USER priority, human-provided
  knowledge/runtime/      — RUNTIME priority, system-verified
  knowledge/learning/     — LEARNING priority, AI candidate pool

No database. No provider. No network. Pure filesystem persistence.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    AliasEntry,
    CandidateStatus,
    ConflictRecord,
    EntityType,
    KnowledgeEntity,
    LearningCandidate,
    PriorityLevel,
    utc_now_iso,
)

STORE_FILES: Dict[str, str] = {
    "characters": "characters.json",
    "glossary": "glossary.json",
    "aliases": "aliases.json",
    "candidates": "candidates.json",
}


def _default_store_root() -> Path:
    return Path("knowledge")


class KnowledgeStore:
    """File-based tiered knowledge store.

    Directory layout:
      knowledge/
        user/
          characters.json
          glossary.json
          aliases.json
        runtime/
          characters.json
          glossary.json
          aliases.json
        learning/
          candidates.json
    """

    def __init__(self, store_root: Optional[str] = None):
        self.root = Path(store_root) if store_root else _default_store_root()

    def ensure_dirs(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for tier in ("user", "runtime", "learning"):
            (self.root / tier).mkdir(parents=True, exist_ok=True)

    def _tier_dir(self, priority: PriorityLevel) -> Path:
        if priority == PriorityLevel.USER:
            return self.root / "user"
        elif priority == PriorityLevel.RUNTIME:
            return self.root / "runtime"
        elif priority == PriorityLevel.LEARNING:
            return self.root / "learning"
        else:
            return self.root / "runtime"

    def _file_path(self, priority: PriorityLevel, kind: str) -> Path:
        return self._tier_dir(priority) / STORE_FILES[kind]

    # ── load / save (entities) ───────────────────────────────

    def _load_json(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _save_json(self, path: Path, data: List[Dict[str, Any]]) -> None:
        self.ensure_dirs()
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    def load_entities(self, priority: PriorityLevel, kind: str = "characters") -> List[KnowledgeEntity]:
        path = self._file_path(priority, kind)
        raw = self._load_json(path)
        return [KnowledgeEntity.from_dict(r) for r in raw]

    def save_entities(
        self,
        entities: List[KnowledgeEntity],
        priority: PriorityLevel,
        kind: str = "characters",
    ) -> None:
        path = self._file_path(priority, kind)
        self._save_json(path, [e.to_dict() for e in entities])

    # ── Load / Save (aliases) ───────────────────────────────

    def load_aliases(self, priority: PriorityLevel) -> List[AliasEntry]:
        path = self._file_path(priority, "aliases")
        raw = self._load_json(path)
        return [AliasEntry.from_dict(r) for r in raw]

    def save_aliases(
        self,
        aliases: List[AliasEntry],
        priority: PriorityLevel,
    ) -> None:
        path = self._file_path(priority, "aliases")
        self._save_json(path, [a.to_dict() for a in aliases])

    # ── Candidates ───────────────────────────────────────────

    def load_candidates(self) -> List[LearningCandidate]:
        path = self.root / "learning" / STORE_FILES["candidates"]
        raw = self._load_json(path)
        return [LearningCandidate.from_dict(r) for r in raw]

    def save_candidates(self, candidates: List[LearningCandidate]) -> None:
        path = self.root / "learning" / STORE_FILES["candidates"]
        self._save_json(path, [c.to_dict() for c in candidates])

    # ── Tier enumeration ─────────────────────────────────────

    def list_all_sources(self) -> Dict[str, List[str]]:
        """Return {priority_tier_name: [source_strings]} for audit."""
        result: Dict[str, List[str]] = {}
        for tier_name, priority in [
            ("user", PriorityLevel.USER),
            ("runtime", PriorityLevel.RUNTIME),
            ("learning", PriorityLevel.LEARNING),
        ]:
            sources: List[str] = []
            for kind in ("characters", "glossary"):
                entities = self.load_entities(priority, kind)
                sources.extend(e.source for e in entities)
            candidates = self.load_candidates()
            sources.extend(c.source for c in candidates)
            result[tier_name] = sorted(set(sources))
        return result

    def entity_count(self, priority: PriorityLevel) -> int:
        count = 0
        for kind in ("characters", "glossary"):
            count += len(self.load_entities(priority, kind))
        return count

    def candidate_count(self) -> int:
        return len(self.load_candidates())

    # ── Full snapshot ────────────────────────────────────────

    def snapshot(self) -> Dict[str, Any]:
        return {
            "user_characters": self.entity_count(PriorityLevel.USER),
            "user_glossary": len(self.load_entities(PriorityLevel.USER, "glossary")),
            "runtime_characters": self.entity_count(PriorityLevel.RUNTIME),
            "runtime_glossary": len(self.load_entities(PriorityLevel.RUNTIME, "glossary")),
            "candidates": self.candidate_count(),
        }