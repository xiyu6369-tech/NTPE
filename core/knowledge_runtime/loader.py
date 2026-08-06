"""RM-6.1.1 Knowledge Loader — dedicated offline domain bundle loaders.

No provider imports. Pure datamodel pipeline.
Source format is intentionally untyped dicts — no coupling to
any external schema, benchmark, or feedback module.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .errors import KnowledgeLoadError
from .models import KnowledgeBundle, KnowledgeEntry, KnowledgePrototype


class KnowledgeLoader:
    """Load knowledge prototypes and bundles from raw source dictionaries.

    The loader accepts plain Python dicts only. There is no import
    from core.knowledge, no provider reference, and no benchmark
    integration. This is an intentionally offline skeleton.
    """

    version = "rm-6.1.1"

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

    def _build_bundle(
        self,
        domain: str,
        bundle_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeBundle:
        prototypes = self.load_domain(domain)
        entries = [
            KnowledgeEntry(
                key=p.key,
                value=p.metadata.get("value", p.key),
                domain=p.domain,
                metadata=dict(p.metadata),
                version=self.version,
            )
            for p in prototypes
        ]
        return KnowledgeBundle(
            id=bundle_id,
            entries=entries,
            domain=domain,
            metadata=dict(metadata or {}),
            version=self.version,
        )

    def load_character_bundle(
        self, metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBundle:
        return self._build_bundle("character", "bundle-character", metadata)

    def load_glossary_bundle(
        self, metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBundle:
        return self._build_bundle("glossary", "bundle-glossary", metadata)

    def load_scene_bundle(
        self, metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBundle:
        return self._build_bundle("scene", "bundle-scene", metadata)

    def load_narrative_bundle(
        self, metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBundle:
        return self._build_bundle("narrative", "bundle-narrative", metadata)

    def load_style_bundle(
        self, metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBundle:
        return self._build_bundle("style", "bundle-style", metadata)

    def load_all_bundles(
        self, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, KnowledgeBundle]:
        """Load all domain bundles from source, skipping empty domains."""
        result: Dict[str, KnowledgeBundle] = {}
        for domain in ("character", "glossary", "scene", "narrative", "style"):
            try:
                result[domain] = self._build_bundle(domain, f"bundle-{domain}", metadata)
            except KnowledgeLoadError:
                pass
        return result

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "knowledge_loader",
            "version": self.version,
            "domains": sorted(self.source.keys()),
            "enabled": True,
        }


__all__ = ["KnowledgeLoader"]