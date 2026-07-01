"""Foundation-08.9 Knowledge integrity checks."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..contracts import KnowledgeQuery
from ..repositories.manager import KnowledgeRepositoryManager


@dataclass
class KnowledgeIntegrityReport:
    valid: bool = True
    issues: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_issue(self, issue_type: str, message: str, **metadata: Any) -> None:
        self.valid = False
        self.issues.append({"type": issue_type, "message": message, "metadata": dict(metadata)})

    def to_dict(self) -> Dict[str, Any]:
        return {"valid": self.valid, "issues": list(self.issues), "metadata": dict(self.metadata)}


class KnowledgeIntegrityChecker:
    """Verify repository shape without coupling to storage implementation."""

    version = "foundation-08.9"

    def __init__(self, repository_manager: Optional[KnowledgeRepositoryManager] = None):
        self.repository_manager = repository_manager or KnowledgeRepositoryManager()

    def check(self) -> KnowledgeIntegrityReport:
        items = self.repository_manager.query(KnowledgeQuery())
        report = KnowledgeIntegrityReport(metadata={"version": self.version, "item_count": len(items)})
        identities = Counter((item.domain, item.key) for item in items)
        for item in items:
            if not item.key:
                report.add_issue("empty_key", "Knowledge item key is empty", domain=item.domain)
            if not item.domain:
                report.add_issue("empty_domain", "Knowledge item domain is empty", key=item.key)
            if item.value is None:
                report.add_issue("empty_value", "Knowledge item value is None", key=item.key, domain=item.domain)
        for (domain, key), count in identities.items():
            if count > 1:
                report.add_issue("duplicate", "Duplicate knowledge item identity", key=key, domain=domain, count=count)
        return report

    def verify_snapshot(self, snapshot: Any) -> KnowledgeIntegrityReport:
        payload = snapshot.to_dict() if hasattr(snapshot, "to_dict") else dict(snapshot or {})
        report = KnowledgeIntegrityReport(metadata={"version": self.version, "kind": "snapshot"})
        if not payload.get("name"):
            report.add_issue("snapshot_name", "Snapshot name is missing")
        if "items" not in payload:
            report.add_issue("snapshot_items", "Snapshot items are missing")
        for index, item in enumerate(payload.get("items") or []):
            if not item.get("key"):
                report.add_issue("snapshot_item_key", "Snapshot item key is missing", index=index)
        return report


def check_knowledge_integrity(repository_manager: Optional[KnowledgeRepositoryManager] = None) -> Dict[str, Any]:
    return KnowledgeIntegrityChecker(repository_manager=repository_manager).check().to_dict()


__all__ = ["KnowledgeIntegrityChecker", "KnowledgeIntegrityReport", "check_knowledge_integrity"]
