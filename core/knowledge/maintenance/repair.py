"""Foundation-08.9 Knowledge repair routines."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from ..contracts import KnowledgeItem, KnowledgeQuery
from ..repositories.manager import KnowledgeRepositoryManager
from .integrity import KnowledgeIntegrityChecker


class KnowledgeRepairEngine:
    """Best-effort repair utilities for normalized knowledge items."""

    version = "foundation-08.9"

    def __init__(self, repository_manager: Optional[KnowledgeRepositoryManager] = None):
        self.repository_manager = repository_manager or KnowledgeRepositoryManager()
        self.integrity = KnowledgeIntegrityChecker(self.repository_manager)

    def detect_duplicates(self) -> List[Dict[str, Any]]:
        items = self.repository_manager.query(KnowledgeQuery())
        seen: Set[Tuple[str, str]] = set()
        duplicates = []
        for item in items:
            identity = (item.domain, item.key)
            if identity in seen:
                duplicates.append(item.to_dict())
            seen.add(identity)
        return duplicates

    def repair_empty_keys(self, prefix: str = "repaired") -> int:
        items = self.repository_manager.query(KnowledgeQuery())
        repaired = 0
        for index, item in enumerate(items):
            if not item.key:
                item.key = f"{prefix}_{index}"
                item.metadata["repaired_by"] = self.version
                self.repository_manager.repository.put(item)
                repaired += 1
        return repaired

    def repair_duplicates(self) -> int:
        items = self.repository_manager.query(KnowledgeQuery())
        seen: Set[Tuple[str, str]] = set()
        repaired = 0
        for item in items:
            identity = (item.domain, item.key)
            if identity in seen:
                new_key = f"{item.key}__duplicate_{repaired + 1}"
                self.repository_manager.repository.delete(item.key, item.domain)
                item.key = new_key
                item.metadata["repaired_by"] = self.version
                self.repository_manager.repository.put(item)
                repaired += 1
            else:
                seen.add(identity)
        return repaired

    def repair_broken_references(self) -> int:
        items = self.repository_manager.query(KnowledgeQuery())
        valid_keys = {item.key for item in items if item.key}
        repaired = 0
        for item in items:
            refs = item.metadata.get("references")
            if isinstance(refs, list):
                next_refs = [ref for ref in refs if ref in valid_keys]
                if next_refs != refs:
                    item.metadata["references"] = next_refs
                    item.metadata["repaired_by"] = self.version
                    self.repository_manager.repository.put(item)
                    repaired += 1
        return repaired

    def auto_repair(self) -> Dict[str, Any]:
        before = self.integrity.check().to_dict()
        result = {
            "version": self.version,
            "empty_keys_repaired": self.repair_empty_keys(),
            "duplicates_repaired": self.repair_duplicates(),
            "broken_references_repaired": self.repair_broken_references(),
        }
        result["before"] = before
        result["after"] = self.integrity.check().to_dict()
        return result


__all__ = ["KnowledgeRepairEngine"]
