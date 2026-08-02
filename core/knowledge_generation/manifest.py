"""
Manifest System for Knowledge Extraction SDK (RM-5.7.2)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import json


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ManifestMetadata:
    version: str = "1.0"
    created_at: str = field(default_factory=utc_now_iso)
    entity_count: int = 0
    schema_version: str = "1.0"
    extractor_version: str = "5.7.2"
    checksum: str = ""
    domains: List[str] = field(default_factory=list)
    source_document: str = ""
    extraction_time_ms: float = 0.0
    validation_passed: bool = True
    compilation_time_ms: float = 0.0
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "created_at": self.created_at,
            "entity_count": self.entity_count,
            "schema_version": self.schema_version,
            "extractor_version": self.extractor_version,
            "checksum": self.checksum,
            "domains": list(self.domains),
            "source_document": self.source_document,
            "extraction_time_ms": self.extraction_time_ms,
            "validation_passed": self.validation_passed,
            "compilation_time_ms": self.compilation_time_ms,
            "custom": dict(self.custom),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ManifestMetadata":
        return cls(
            version=data.get("version", "1.0"),
            created_at=data.get("created_at", utc_now_iso()),
            entity_count=data.get("entity_count", 0),
            schema_version=data.get("schema_version", "1.0"),
            extractor_version=data.get("extractor_version", "5.7.2"),
            checksum=data.get("checksum", ""),
            domains=data.get("domains", []),
            source_document=data.get("source_document", ""),
            extraction_time_ms=data.get("extraction_time_ms", 0.0),
            validation_passed=data.get("validation_passed", True),
            compilation_time_ms=data.get("compilation_time_ms", 0.0),
            custom=data.get("custom", {}),
        )
class KnowledgeManifest:
    def __init__(self, metadata: ManifestMetadata = None):
        self.metadata = metadata or ManifestMetadata()
        self._entity_hashes: Dict[str, str] = {}
    
    def add_entity_hash(self, entity_id: str, entity_hash: str) -> None:
        self._entity_hashes[entity_id] = entity_hash
    
    def compute_checksum(self, data: Dict[str, Any]) -> str:
        content = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    
    def update_checksum(self, compiled_data: Dict[str, Any]) -> None:
        self.metadata.checksum = self.compute_checksum(compiled_data)
    
    def to_dict(self) -> Dict[str, Any]:
        return {"metadata": self.metadata.to_dict(), "entity_hashes": dict(self._entity_hashes)}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeManifest":
        manifest = cls(ManifestMetadata.from_dict(data.get("metadata", {})))
        manifest._entity_hashes = data.get("entity_hashes", {})
        return manifest
    
    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, path: str) -> "KnowledgeManifest":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


class ManifestBuilder:
    def __init__(self):
        self.metadata = ManifestMetadata()
        self.entity_hashes: Dict[str, str] = {}
    
    def with_version(self, version: str) -> "ManifestBuilder":
        self.metadata.version = version
        return self
    
    def with_entity_count(self, count: int) -> "ManifestBuilder":
        self.metadata.entity_count = count
        return self
    
    def with_schema_version(self, version: str) -> "ManifestBuilder":
        self.metadata.schema_version = version
        return self
    
    def with_extractor_version(self, version: str) -> "ManifestBuilder":
        self.metadata.extractor_version = version
        return self
    
    def with_domains(self, domains: List[str]) -> "ManifestBuilder":
        self.metadata.domains = domains
        return self
    
    def with_source_document(self, doc_id: str) -> "ManifestBuilder":
        self.metadata.source_document = doc_id
        return self
    
    def with_extraction_time(self, time_ms: float) -> "ManifestBuilder":
        self.metadata.extraction_time_ms = time_ms
        return self
    
    def with_compilation_time(self, time_ms: float) -> "ManifestBuilder":
        self.metadata.compilation_time_ms = time_ms
        return self
    
    def with_validation_status(self, passed: bool) -> "ManifestBuilder":
        self.metadata.validation_passed = passed
        return self
    
    def with_custom(self, key: str, value: Any) -> "ManifestBuilder":
        self.metadata.custom[key] = value
        return self
    
    def add_entity_hash(self, entity_id: str, entity_hash: str) -> "ManifestBuilder":
        self.entity_hashes[entity_id] = entity_hash
        return self
    
    def build(self) -> KnowledgeManifest:
        manifest = KnowledgeManifest(self.metadata)
        manifest._entity_hashes = self.entity_hashes
        return manifest


def build_knowledge_manifest(
    entities: List[Any],
    domains: List[str],
    source_document: str = "",
    extraction_time_ms: float = 0.0,
    compilation_time_ms: float = 0.0,
    validation_passed: bool = True,
    schema_version: str = "1.0",
    extractor_version: str = "5.7.2",
    **custom
) -> KnowledgeManifest:
    builder = ManifestBuilder()
    builder.with_entity_count(len(entities))
    builder.with_domains(domains)
    builder.with_source_document(source_document)
    builder.with_extraction_time(extraction_time_ms)
    builder.with_compilation_time(compilation_time_ms)
    builder.with_validation_status(validation_passed)
    builder.with_schema_version(schema_version)
    builder.with_extractor_version(extractor_version)
    for key, value in custom.items():
        builder.with_custom(key, value)
    return builder.build()
