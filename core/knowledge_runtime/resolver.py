"""RM-6.1.0 Knowledge Resolver — resolves prototypes into entries.

No provider imports. Pure offline resolution from loaded prototypes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .errors import KnowledgeResolveError
from .models import KnowledgeEntry, KnowledgePrototype


class KnowledgeResolver:
    """Resolve KnowledgePrototypes into KnowledgeEntry values.

    Resolution logic is entirely local. No provider or external
    service is invoked. This is the offline contract of RM-6.1.
    """

    version = "rm-6.1.0"

    def __init__(self, prototypes: Optional[List[KnowledgePrototype]] = None):
        self.prototypes: List[KnowledgePrototype] = prototypes or []
        self._index: Dict[str, Dict[str, KnowledgePrototype]] = {}

    def index_prototypes(self) -> "KnowledgeResolver":
        self._index.clear()
        for proto in self.prototypes:
            self._index.setdefault(proto.domain, {})[proto.key] = proto
        return self

    def resolve(self, key: str, domain: str = "general") -> KnowledgeEntry:
        proto = self.find_prototype(key, domain)
        if proto is None:
            raise KnowledgeResolveError(f"Cannot resolve {domain}:{key}")
        return KnowledgeEntry(
            key=proto.key,
            value=proto.metadata.get("value", key),
            domain=proto.domain,
            metadata=dict(proto.metadata),
            version=self.version,
        )

    def find_prototype(self, key: str, domain: str = "general") -> Optional[KnowledgePrototype]:
        domain_index = self._index.get(domain, {})
        return domain_index.get(key)

    def resolve_all(self) -> List[KnowledgeEntry]:
        self.index_prototypes()
        result: List[KnowledgeEntry] = []
        for proto in self.prototypes:
            entry = KnowledgeEntry(
                key=proto.key,
                value=proto.metadata.get("value", proto.key),
                domain=proto.domain,
                metadata=dict(proto.metadata),
                version=self.version,
            )
            result.append(entry)
        return result

    def resolve_domain(self, domain: str) -> List[KnowledgeEntry]:
        self.index_prototypes()
        domain_index = self._index.get(domain, {})
        return [
            KnowledgeEntry(
                key=proto.key,
                value=proto.metadata.get("value", proto.key),
                domain=proto.domain,
                metadata=dict(proto.metadata),
                version=self.version,
            )
            for proto in domain_index.values()
        ]

    @property
    def domain_keys(self) -> List[str]:
        self.index_prototypes()
        return sorted(self._index.keys())

    def manifest(self) -> Dict[str, Any]:
        self.index_prototypes()
        return {
            "name": "knowledge_resolver",
            "version": self.version,
            "prototype_count": len(self.prototypes),
            "domains": self.domain_keys,
            "enabled": True,
        }


__all__ = ["KnowledgeResolver"]