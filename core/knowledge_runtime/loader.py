"""RM-6.1.1 Knowledge Loader — dedicated offline domain bundle loaders.

No provider imports. Pure datamodel pipeline.
Source format is intentionally untyped dicts — no coupling to
any external schema, benchmark, or feedback module.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .errors import KnowledgeLoadError
from .models import KnowledgeBundle, KnowledgeEntry, KnowledgePrototype


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def to_canonical_json(obj: dict) -> str:
    """Deterministic JSON: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class SeriesKnowledge:
    """Series-canonical knowledge for Novel tier population."""
    schema_name: str = "ntpe.series_knowledge"
    schema_version: str = "1.0"
    series_id: str = ""
    character_entries: Dict[str, Any] = field(default_factory=dict)
    glossary_entries: Dict[str, Any] = field(default_factory=dict)
    general_entries: Dict[str, Any] = field(default_factory=dict)
    knowledge_hash: str = ""

    def to_dict(self, include_knowledge_hash: bool = True) -> Dict[str, Any]:
        payload = {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "series_id": self.series_id,
            "character_entries": self.character_entries,
            "glossary_entries": self.glossary_entries,
            "general_entries": self.general_entries,
        }
        if include_knowledge_hash:
            payload["knowledge_hash"] = self.knowledge_hash
        return payload


@dataclass(frozen=True)
class KnowledgePopulationReport:
    """Report of Series -> KnowledgeRuntime population."""
    series_id: str
    character_terms_populated: int
    glossary_terms_populated: int
    general_facts_populated: int
    knowledge_hash: str
    source_memory_hash: str
    source_glossary_hash: str


class SeriesKnowledgeValidationError(Exception):
    """Raised when SeriesKnowledge schema validation fails."""
    pass


class SeriesKnowledgeIntegrityError(Exception):
    """Raised when SeriesKnowledge fingerprint verification fails (fail-closed)."""
    pass


def compute_series_knowledge_fingerprint(series_knowledge_dict: dict) -> str:
    """Compute SHA-256 of canonical knowledge payload (excluding knowledge_hash itself)."""
    payload = {k: v for k, v in series_knowledge_dict.items() if k != "knowledge_hash"}
    canonical = to_canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def get_series_knowledge_path(output_root: Path, series_id: str) -> Path:
    """Get the path for series knowledge file."""
    series_dir = output_root / "series" / series_id
    return series_dir / f"series_knowledge_{series_id}.json"


def save_series_knowledge(series_knowledge: SeriesKnowledge, path: Path) -> None:
    """Save SeriesKnowledge to disk with atomic write and fingerprint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    data = series_knowledge.to_dict(include_knowledge_hash=True)
    temp_path.write_text(
        to_canonical_json(data),
        encoding="utf-8"
    )
    temp_path.replace(path)


def load_series_knowledge_from_path(path: Path, expected_series_id: str) -> SeriesKnowledge:
    """Load SeriesKnowledge from disk with integrity verification (fail-closed)."""
    if not path.exists():
        # Return empty knowledge for fresh series
        return SeriesKnowledge(
            schema_name="ntpe.series_knowledge",
            schema_version="1.0",
            series_id=expected_series_id,
            character_entries={},
            glossary_entries={},
            general_entries={},
            knowledge_hash="",
        )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SeriesKnowledgeValidationError(f"Invalid JSON in knowledge file: {e}")

    # Schema validation
    if data.get("schema_name") != "ntpe.series_knowledge":
        raise SeriesKnowledgeValidationError(f"Invalid schema_name: {data.get('schema_name')}")
    if data.get("schema_version") != "1.0":
        raise SeriesKnowledgeValidationError(f"Invalid schema_version: {data.get('schema_version')}")
    if data.get("series_id") != expected_series_id:
        raise SeriesKnowledgeValidationError(f"Series ID mismatch: expected {expected_series_id}, got {data.get('series_id')}")

    # Fingerprint verification (fail-closed)
    stored_hash = data.get("knowledge_hash", "")
    if stored_hash:
        computed_hash = compute_series_knowledge_fingerprint(data)
        if stored_hash != computed_hash:
            raise SeriesKnowledgeIntegrityError(f"Knowledge fingerprint mismatch: stored={stored_hash}, computed={computed_hash}")

    return SeriesKnowledge(
        schema_name=data["schema_name"],
        schema_version=data["schema_version"],
        series_id=data["series_id"],
        character_entries=data.get("character_entries", {}),
        glossary_entries=data.get("glossary_entries", {}),
        general_entries=data.get("general_entries", {}),
        knowledge_hash=stored_hash,
    )


def load_series_knowledge(series_id: str, output_root: Path) -> SeriesKnowledge:
    """Load SeriesKnowledge from output root with integrity verification."""
    path = get_series_knowledge_path(output_root, series_id)
    return load_series_knowledge_from_path(path, series_id)


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

    def load_series_character_knowledge(
        self,
        series_memory_store: Any,  # SeriesMemoryStore from core.series_memory
    ) -> Dict[str, Any]:
        """
        Load character canonical facts for Novel tier.

        Returns dict suitable for KnowledgeMerger.set_novel("character", entries).
        Only APPROVED NEVER-expiry facts from SeriesMemoryStore.
        """
        from core.character_memory_v2.models import FactType

        entries = {}
        for record in series_memory_store.get_all_canonical_facts():
            # Canonical names
            if record.fact_type == FactType.CANONICAL_NAME:
                entries[f"char:{record.korean_name}"] = record.canonical_name
                for alias in record.aliases:
                    entries[f"alias:{alias}"] = record.canonical_name
            # Relationships
            elif record.fact_type == FactType.RELATIONSHIP:
                entries[f"rel:{record.korean_name}:{record.value}"] = record.value
            # Terminology preferences
            elif record.fact_type == FactType.TERMINOLOGY_PREFERENCE:
                entries[f"term:{record.korean_name}"] = record.value
            # World facts / background / physical traits / personality
            elif record.fact_type in (FactType.OTHER, FactType.APPEARANCE, FactType.PERSONALITY_TRAIT):
                entries[f"fact:{record.fact_type.value.lower()}:{record.korean_name}"] = record.value
        return entries

    def load_series_glossary_knowledge(
        self,
        series_glossary: Any,  # SeriesGlossary from core.glossary_builder
    ) -> Dict[str, Any]:
        """
        Load locked glossary terms for Novel tier.

        Returns dict suitable for KnowledgeMerger.set_novel("glossary", entries).
        Uses SeriesGlossary.get_locked_dictionary() adapter.
        """
        return series_glossary.get_locked_dictionary()

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "knowledge_loader",
            "version": self.version,
            "domains": sorted(self.source.keys()),
            "enabled": True,
        }


__all__ = [
    "KnowledgeLoader",
    "SeriesKnowledge",
    "KnowledgePopulationReport",
    "SeriesKnowledgeValidationError",
    "SeriesKnowledgeIntegrityError",
    "compute_series_knowledge_fingerprint",
    "get_series_knowledge_path",
    "save_series_knowledge",
    "load_series_knowledge_from_path",
    "load_series_knowledge",
    "utc_now_iso",
    "to_canonical_json",
]