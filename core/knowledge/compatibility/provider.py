"""
RM-5.7.5 Knowledge Package Provider.

READ-ONLY provider for Translation Runtime.
This is the ONLY interface Runtime may use to access Knowledge Packages.

PROHIBITED for Runtime:
- Extractor (core.knowledge_generation)
- Compiler (core.knowledge_compilation)
- Review Engine (core.knowledge_review)
- Validator (core.knowledge_validation)
- Any generation pipeline component
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.knowledge_compilation.package_builder import PackageReader, create_package_reader
from core.knowledge_compilation.models import CompilationPackage, CompilationManifest
from core.knowledge_compilation.checksum import ChecksumCalculator, DEFAULT_CALCULATOR


@dataclass(frozen=True, slots=True)
class EntityQuery:
    """Query parameters for entity retrieval."""
    entity_type: str
    entity_id: Optional[str] = None
    name: Optional[str] = None
    limit: Optional[int] = None
    domain: Optional[str] = None



class KnowledgePackageProvider:
    """
    Read-only provider for Frozen Knowledge Packages.

    This is the SINGLE interface Runtime must use.
    All entity access goes through typed methods: get_character(), get_glossary(), etc.
    """

    # Supported entity types
    ENTITY_TYPES = ("character", "glossary", "scene", "narrative", "style")

    def __init__(
        self,
        package_dir: str | Path,
        verify_on_load: bool = True,
        calculator: ChecksumCalculator | None = None,
    ) -> None:
        """
        Initialize provider with a Frozen Knowledge Package directory.

        Args:
            package_dir: Path to package directory (e.g., artifacts/knowledge_packages/v1)
            verify_on_load: If True, verify package integrity on initialization
            calculator: Checksum calculator (uses default if not provided)
        """
        self._package_dir = Path(package_dir)
        self._calculator = calculator or DEFAULT_CALCULATOR
        self._reader = create_package_reader(self._package_dir)
        self._package: CompilationPackage | None = None
        self._manifest: CompilationManifest | None = None
        self._entity_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._verified = False

        if verify_on_load:
            self.verify()

    @property
    def package_dir(self) -> Path:
        """Return the package directory path."""
        return self._package_dir

    @property
    def package(self) -> CompilationPackage:
        """Lazy-load the full compilation package."""
        if self._package is None:
            self._package = self._reader.package
        return self._package

    @property
    def manifest(self) -> CompilationManifest:
        """Lazy-load the manifest."""
        if self._manifest is None:
            self._manifest = self._reader.manifest
        return self._manifest

    # === Typed Entity Access Methods (Runtime API) ===

    def get_character(self, entity_id: str | None = None, name: str | None = None) -> List[Dict[str, Any]]:
        """Get character entities. Filter by entity_id or name if provided."""
        return self._get_entities("character", entity_id, name)

    def get_glossary(self, entity_id: str | None = None, name: str | None = None) -> List[Dict[str, Any]]:
        """Get glossary entities. Filter by entity_id or name if provided."""
        return self._get_entities("glossary", entity_id, name)

    def get_scene(self, entity_id: str | None = None, name: str | None = None) -> List[Dict[str, Any]]:
        """Get scene entities. Filter by entity_id or name if provided."""
        return self._get_entities("scene", entity_id, name)

    def get_narrative(self, entity_id: str | None = None, name: str | None = None) -> List[Dict[str, Any]]:
        """Get narrative entities. Filter by entity_id or name if provided."""
        return self._get_entities("narrative", entity_id, name)

    def get_style(self, entity_id: str | None = None, name: str | None = None) -> List[Dict[str, Any]]:
        """Get style entities. Filter by entity_id or name if provided."""
        return self._get_entities("style", entity_id, name)

    def get_entities(self, entity_type: str, entity_id: str | None = None, name: str | None = None) -> List[Dict[str, Any]]:
        """
        Generic entity retrieval.

        Args:
            entity_type: One of "character", "glossary", "scene", "narrative", "style"
            entity_id: Optional entity ID filter
            name: Optional name filter

        Returns:
            List of matching entities
        """
        if entity_type not in self.ENTITY_TYPES:
            raise ValueError(f"Unknown entity type: {entity_type}. Supported: {self.ENTITY_TYPES}")
        return self._get_entities(entity_type, entity_id, name)

    # === Internal Methods ===

    def _get_entities(self, entity_type: str, entity_id: str | None, name: str | None) -> List[Dict[str, Any]]:
        """Internal method to get and filter entities."""
        if entity_type not in self._entity_cache:
            self._entity_cache[entity_type] = self._reader.get_entities(entity_type)

        entities = self._entity_cache[entity_type]

        if entity_id is not None:
            entities = [e for e in entities if e.get("entity_id") == entity_id]

        if name is not None:
            entities = [e for e in entities if e.get("name") == name]

        return entities

    # === Package Metadata ===

    def get_package_info(self) -> Dict[str, Any]:
        """Get package metadata without loading full entities."""
        return {
            "package_id": self.manifest.package_id,
            "package_version": self.manifest.package_version,
            "schema_versions": dict(self.manifest.schema_versions),
            "entity_counts": dict(self.manifest.entity_counts),
            "created_at": self.manifest.created_at,
            "compiler_version": self.manifest.compiler_version,
            "checksum": self.package.checksum,
        }

    def get_entity_types(self) -> List[str]:
        """Return list of entity types present in the package."""
        return self.package.get_entity_types()

    def get_entity_count(self, entity_type: str) -> int:
        """Get count of entities for a specific type."""
        return self.package.get_entity_count(entity_type)

    def total_entity_count(self) -> int:
        """Get total entity count across all types."""
        return self.package.total_entity_count()

    # === Verification ===

    def verify(self) -> bool:
        """
        Verify package integrity (checksum, manifest, structure).

        Returns:
            True if package is valid

        Raises:
            ValueError: If verification fails
        """
        # Verify checksum
        if not self.package.verify_checksum(self._calculator):
            raise ValueError(f"Checksum verification failed for package at {self._package_dir}")

        # Verify manifest matches entities
        for entity_type, count in self.manifest.entity_counts.items():
            actual = self.package.get_entity_count(entity_type)
            if actual != count:
                raise ValueError(
                    f"Manifest entity count mismatch for {entity_type}: "
                    f"manifest={count}, actual={actual}"
                )

        # Verify all required files exist
        for entity_type in self.ENTITY_TYPES:
            if entity_type in self.manifest.entity_counts:
                plural_map = {"glossary": "glossaries"}
                plural = plural_map.get(entity_type, f"{entity_type}s")
                file_path = self._package_dir / f"{plural}.json"
                if not file_path.exists():
                    raise ValueError(f"Required entity file missing: {file_path}")

        manifest_path = self._package_dir / "manifest.json"
        if not manifest_path.exists():
            raise ValueError(f"Manifest file missing: {manifest_path}")

        self._verified = True
        return True

    def is_verified(self) -> bool:
        """Return whether package has been verified."""
        return self._verified

    # === Context Building (for Prompt Pipeline) ===

    def build_context(self, entity_types: List[str] | None = None) -> Dict[str, Any]:
        """
        Build knowledge context for prompt attachment.

        Args:
            entity_types: Optional list of entity types to include (default: all)

        Returns:
            Context dictionary compatible with prompt pipeline
        """
        types = entity_types or self.get_entity_types()
        domains: Dict[str, Dict[str, Any]] = {}
        items: List[Dict[str, Any]] = []

        for entity_type in types:
            entities = self._get_entities(entity_type, None, None)
            for entity in entities:
                key = entity.get("entity_id", entity.get("name", ""))
                domains.setdefault(entity_type, {})[key] = entity
                items.append(entity)

        return {
            "type": "knowledge_context",
            "version": "rm-5.7.5",
            "items": items,
            "domains": domains,
            "manifest": self.manifest.to_dict(),
        }

    def attach_to_prompt_package(self, prompt_package: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Attach knowledge context to a prompt package."""
        next_package = dict(prompt_package or {})
        components = list(next_package.get("context_components", []))
        components.append(self.build_context())
        next_package["context_components"] = components
        return next_package


def create_provider(package_dir: str | Path, verify_on_load: bool = True) -> KnowledgePackageProvider:
    """Convenience function to create a KnowledgePackageProvider."""
    return KnowledgePackageProvider(package_dir, verify_on_load=verify_on_load)


__all__ = [
    "KnowledgePackageProvider",
    "EntityQuery",
    "create_provider",
]
