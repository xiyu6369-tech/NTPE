"""
RM-5.7.5 Legacy Mapper - v1 to v2 mapping.

Maps legacy knowledge paths to Frozen Knowledge Package v2 structure.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

@dataclass(frozen=True, slots=True)
class LegacyMapping:
    """Represents a legacy path to v2 package mapping."""
    legacy_path: str
    entity_type: str  # character, glossary, scene, narrative, style
    v2_package_path: str  # e.g., "artifacts/knowledge_packages/v1/characters.json"
    description: str



class LegacyMapper:
    """Maps legacy knowledge sources to Frozen Knowledge Package v2."""

    # Legacy to v2 entity type mapping
    LEGACY_ENTITY_MAP = {
        "character_memory.json": "character",
        "glossary.json": "glossary",
        "knowledge_base.json": "character",  # contains characters + glossary
        "character_match_dictionary.json": "character",
        "character_alias_index.json": "character",
    }

    # V2 package file names (with irregular plurals)
    V2_FILE_MAP = {
        "character": "characters.json",
        "glossary": "glossaries.json",
        "scene": "scenes.json",
        "narrative": "narrative.json",
        "style": "style.json",
    }

    def __init__(self, v2_package_root: str | Path = "artifacts/knowledge_packages/v1"):
        self._v2_root = Path(v2_package_root)

    def get_legacy_mappings(self) -> List[LegacyMapping]:
        """Get all legacy to v2 mappings."""
        mappings = []
        for legacy_name, entity_type in self.LEGACY_ENTITY_MAP.items():
            v2_file = self.V2_FILE_MAP.get(entity_type, f"{entity_type}s.json")
            v2_path = self._v2_root / v2_file
            mappings.append(LegacyMapping(
                legacy_path=f"memory/{legacy_name}",
                entity_type=entity_type,
                v2_package_path=str(v2_path),
                description=f"Legacy {legacy_name} mapped to v2 {entity_type} package"
            ))

        # Add glossary.txt as special case
        mappings.append(LegacyMapping(
            legacy_path="data/glossary.txt",
            entity_type="glossary",
            v2_package_path=str(self._v2_root / "glossaries.json"),
            description="Legacy flat glossary.txt mapped to v2 structured glossary package"
        ))

        return mappings

    def get_v2_path(self, entity_type: str) -> Path:
        """Get the v2 package file path for an entity type."""
        v2_file = self.V2_FILE_MAP.get(entity_type, f"{entity_type}s.json")
        return self._v2_root / v2_file

    def get_legacy_path(self, entity_type: str) -> Optional[str]:
        """Get the legacy path for an entity type (reverse lookup)."""
        for legacy, etype in self.LEGACY_ENTITY_MAP.items():
            if etype == entity_type:
                return f"memory/{legacy}"
        return None

    def list_legacy_paths(self) -> List[str]:
        """List all known legacy paths."""
        paths = [f"memory/{name}" for name in self.LEGACY_ENTITY_MAP.keys()]
        paths.append("data/glossary.txt")
        return paths

    def list_v2_paths(self) -> List[str]:
        """List all v2 package file paths."""
        return [str(self._v2_root / f) for f in self.V2_FILE_MAP.values()]


def create_legacy_mapper(v2_package_root: str | Path = "artifacts/knowledge_packages/v1") -> LegacyMapper:
    """Convenience function to create a LegacyMapper."""
    return LegacyMapper(v2_package_root)


__all__ = [
    "LegacyMapper",
    "LegacyMapping",
    "create_legacy_mapper",
]
