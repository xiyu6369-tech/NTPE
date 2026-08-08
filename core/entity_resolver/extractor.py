"""RM-7.2 Entity Extractor.

Extracts known Korean entities from translation chunks.
Does NOT translate - only identifies entities that need resolution.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from .models import EntityType, ExtractedEntity


# Korean name pattern: 2-4 Hangul syllables (typical Korean names)
KOREAN_NAME_PATTERN = re.compile(r"[가-힣]{2,4}")

# Known entity markers from glossary/character data
# These will be populated from knowledge runtime


@dataclass
class EntityExtractor:
    """Extract entities from Korean text chunks."""

    known_entities: Dict[str, str] = None  # source -> entity_type
    custom_patterns: List[re.Pattern] = None

    def __post_init__(self):
        if self.known_entities is None:
            self.known_entities = {}
        if self.custom_patterns is None:
            self.custom_patterns = []

    def extract(self, chunk: str) -> List[ExtractedEntity]:
        """Extract all known entities from a chunk.

        Args:
            chunk: Korean source text

        Returns:
            List of ExtractedEntity found in chunk (in order of appearance)
        """
        if not chunk:
            return []

        extracted = []
        # Track extracted (source, position) pairs to avoid duplicates
        extracted_pairs: Set[tuple[str, int]] = set()

        # First pass: exact matches from known entities (longest first)
        # Process longest first so that longer matches are found before shorter substrings
        for source in sorted(self.known_entities.keys(), key=len, reverse=True):
            entity_type = self.known_entities.get(source, EntityType.UNKNOWN.value)
            # Find ALL positions
            start = 0
            while True:
                found = chunk.find(source, start)
                if found == -1:
                    break
                # Avoid duplicate extractions at same position
                if (source, found) not in extracted_pairs:
                    # Get context (surrounding 20 chars)
                    ctx_start = max(0, found - 20)
                    ctx_end = min(len(chunk), found + len(source) + 20)
                    context = chunk[ctx_start:ctx_end]
                    extracted.append(ExtractedEntity(
                        source=source,
                        entity_type=entity_type,
                        context=context,
                        position=found,
                    ))
                    extracted_pairs.add((source, found))
                start = found + 1

        # Sort by position to maintain text order
        extracted.sort(key=lambda e: e.position)

        # Also extract with custom patterns for entities not in known_entities
        if self.custom_patterns:
            pattern_extracted = self.extract_with_patterns(chunk)
            # Merge, avoiding duplicates by source AND position
            for pe in pattern_extracted:
                if (pe.source, pe.position) not in extracted_pairs:
                    extracted.append(pe)
            extracted.sort(key=lambda e: e.position)

        return extracted

    def extract_with_patterns(self, chunk: str) -> List[ExtractedEntity]:
        """Extract entities using regex patterns (for unknown entities).

        This is a fallback for entities not in known_entities.
        """
        if not chunk:
            return []

        extracted = []
        seen: Set[str] = set()

        # Check custom patterns first
        for pattern in self.custom_patterns:
            for match in pattern.finditer(chunk):
                source = match.group()
                if source not in seen and len(source) >= 2:
                    ctx_start = max(0, match.start() - 20)
                    ctx_end = min(len(chunk), match.end() + 20)
                    context = chunk[ctx_start:ctx_end]
                    extracted.append(ExtractedEntity(
                        source=source,
                        entity_type=EntityType.UNKNOWN.value,
                        context=context,
                        position=match.start(),
                    ))
                    seen.add(source)

        # Fallback: Korean name-like patterns (2-4 syllables)
        # Only if not already captured
        for match in KOREAN_NAME_PATTERN.finditer(chunk):
            source = match.group()
            if source not in seen and source not in self.known_entities:
                ctx_start = max(0, match.start() - 20)
                ctx_end = min(len(chunk), match.end() + 20)
                context = chunk[ctx_start:ctx_end]
                extracted.append(ExtractedEntity(
                    source=source,
                    entity_type=EntityType.UNKNOWN.value,
                    context=context,
                    position=match.start(),
                ))
                seen.add(source)

        extracted.sort(key=lambda e: e.position)
        return extracted

    def update_known_entities(self, entities: Dict[str, str]) -> None:
        """Update known entities from knowledge runtime.

        Args:
            entities: Dict mapping source entity name -> entity_type
        """
        self.known_entities.update(entities)

    def clear(self) -> None:
        """Clear known entities."""
        self.known_entities.clear()


def build_known_entities_from_runtime(runtime) -> Dict[str, str]:
    """Build known entities dict from MergedRuntime.

    Args:
        runtime: MergedRuntime from knowledge_runtime

    Returns:
        Dict mapping Korean entity name -> entity_type
    """
    known = {}

    # Character domain
    char_domain = runtime.get_domain("character")
    if char_domain:
        for key in char_domain.entries.keys():
            known[key] = EntityType.CHARACTER.value

    # Glossary domain (terminology)
    gloss_domain = runtime.get_domain("glossary")
    if gloss_domain:
        for key in gloss_domain.entries.keys():
            known[key] = EntityType.TERMINOLOGY.value

    # Scene domain (places)
    scene_domain = runtime.get_domain("scene")
    if scene_domain:
        for key in scene_domain.entries.keys():
            known[key] = EntityType.PLACE.value

    # Organization could come from narrative or custom domain
    narr_domain = runtime.get_domain("narrative")
    if narr_domain:
        for key in narr_domain.entries.keys():
            # Check if it looks like an organization
            if any(kw in key.lower() for kw in ["회사", "기관", "조직", "단체", "부서", "팀", "과", "실"]):
                known[key] = EntityType.ORGANIZATION.value

    return known


__all__ = [
    "EntityExtractor",
    "build_known_entities_from_runtime",
    "KOREAN_NAME_PATTERN",
]