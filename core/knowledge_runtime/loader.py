"""RM-6.1.0 Knowledge Loader — loads prototypes from offline source.

No provider imports. Pure datamodel pipeline.
Source format is intentionally untyped dicts — no coupling to
any external schema, benchmark, or feedback module.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .errors import KnowledgeLoadError
from .models import KnowledgePrototype


class KnowledgeLoader:
    """Load knowledge prototypes from a raw source dictionary.

    The loader accepts plain Python dicts only. There is no import
    from core.knowledge, no provider reference, and no benchmark
    integration. This is an intentionally offline skeleton.
    """

    version = "rm-6.1.0"

    def __init__(self, source: Optional[Dict[str, Any]] = None):
        self.source = dict(source or {})

    def load_domain(self, domain: str) -> List[KnowledgePrototype]:
        raw_entries = self.source.get(domain, [])
        entries = self._normalize(raw_entries, domain)
        if not entries:
            raise KnowledgeLoadError(f"No entries found for domain: {domain}")
        return entries

    def load_all(self) -> Dict[str, List[KnowledgePrototype]]:
        result: Dict[str, List[KnowledgePrototype]] = {}
        for domain in self.source:
            try:
                result[domain] = self.load_domain(domain)
            except KnowledgeLoadError:
                result[domain] = []
        return result

    def load_keys(self, domain: str, keys: Iterable[str]) -> List[KnowledgePrototype]:
        all_entries = self._normalize(self.source.get(domain, []), domain=domain)
        return [entry for entry in all_entries if entry.key in set(keys)]

    def _normalize(self, raw: Any, domain: str = "general") -> List[KnowledgePrototype]:
        if isinstance(raw, dict):
            return [
                KnowledgePrototype(
                    key=str(key),
                    domain=domain,
                    metadata=dict(value) if isinstance(value, dict) else {"value": value},
                )
                for key, value in raw.items()
            ]
        if isinstance(raw, list):
            return [
                KnowledgePrototype(
                    key=str(item.get("key", "")),
                    domain=domain,
                    metadata=dict(item.get("metadata", {})),
                )
                for item in raw
                if isinstance(item, dict)
            ]
        return []

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "knowledge_loader",
            "version": self.version,
            "domains": sorted(self.source.keys()),
            "enabled": True,
        }


__all__ = ["KnowledgeLoader"]