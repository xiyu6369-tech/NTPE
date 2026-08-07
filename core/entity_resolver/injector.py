"""RM-7.2 Entity Injector.

Injects resolved entities into Prompt as 'Entity Mapping' section.
Only injects entities that appear in the current chunk.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.prompt_runtime.models import PromptSection
from .models import (
    EntityInjectionSet,
    InjectionSource,
    ResolvedEntity,
    UNKNOWN_TRANSLATION,
)


ENTITY_MAPPING_SECTION_NAME = "Entity Mapping"
ENTITY_MAPPING_VERSION = "rm-7.2.0"


class EntityInjector:
    """Inject entity mappings into prompt sections."""

    def __init__(
        self,
        include_unknown: bool = True,
        unknown_marker: str = "(No predefined translation)",
        group_by_type: bool = True,
    ):
        self.include_unknown = include_unknown
        self.unknown_marker = unknown_marker
        self.group_by_type = group_by_type

    def inject(self, injection_set: EntityInjectionSet) -> PromptSection:
        """Convert EntityInjectionSet to PromptSection.

        Args:
            injection_set: Resolved entities for current chunk

        Returns:
            PromptSection named 'Entity Mapping'
        """
        content = self._format_content(injection_set)

        metadata = {
            "entity_count": injection_set.count,
            "known_count": len(injection_set.get_known_entities()),
            "unknown_count": len(injection_set.get_unknown_entities()),
            "source_breakdown": injection_set.metadata,
        }

        return PromptSection(
            name=ENTITY_MAPPING_SECTION_NAME,
            content=content,
            metadata=metadata,
            version=ENTITY_MAPPING_VERSION,
        )

    def _format_content(self, injection_set: EntityInjectionSet) -> str:
        """Format entities as prompt content."""
        if injection_set.count == 0:
            return "No entities found in current chunk."

        known_entities = injection_set.get_known_entities()
        unknown_entities = injection_set.get_unknown_entities()

        # If include_unknown is False and no known entities, return minimal message
        if not self.include_unknown and not known_entities:
            return "No predefined entity translations for this chunk."

        lines = []

        if self.group_by_type:
            # Group by entity type
            by_type: Dict[str, List[ResolvedEntity]] = {}
            for entity in injection_set.entities:
                if not self.include_unknown and not entity.is_known:
                    continue
                etype = entity.entity_type or "UNKNOWN"
                by_type.setdefault(etype, []).append(entity)

            for etype in ["CHARACTER", "PLACE", "ORGANIZATION", "TERMINOLOGY", "UNKNOWN"]:
                entities = by_type.get(etype, [])
                if not entities:
                    continue

                lines.append(f"## {etype}")
                for entity in entities:
                    lines.append(self._format_entity(entity))
                lines.append("")  # Blank line between groups
        else:
            # Flat list
            for entity in injection_set.entities:
                if not self.include_unknown and not entity.is_known:
                    continue
                lines.append(self._format_entity(entity))

        return "\n".join(lines).strip()

    def _format_entity(self, entity: ResolvedEntity) -> str:
        """Format a single entity line."""
        target = entity.target

        # Mark unknown translations - use custom unknown_marker
        if entity.source_level == InjectionSource.AUTO.value and target == UNKNOWN_TRANSLATION:
            return f"{entity.source} → {self.unknown_marker}"

        # Mark user overrides
        if entity.is_user_override:
            return f"{entity.source} → {target} [USER OVERRIDE]"

        # Mark source level for others
        level_marker = f" [{entity.source_level}]"
        return f"{entity.source} → {target}{level_marker}"

    def inject_minimal(self, injection_set: EntityInjectionSet) -> PromptSection:
        """Minimal injection - only known entities, no markers."""
        known = injection_set.get_known_entities()
        if not known:
            return PromptSection(
                name=ENTITY_MAPPING_SECTION_NAME,
                content="No predefined entity translations for this chunk.",
                metadata={"entity_count": 0, "known_count": 0},
                version=ENTITY_MAPPING_VERSION,
            )

        lines = [f"{e.source} → {e.target}" for e in known]
        return PromptSection(
            name=ENTITY_MAPPING_SECTION_NAME,
            content="\n".join(lines),
            metadata={
                "entity_count": len(known),
                "known_count": len(known),
                "mode": "minimal",
            },
            version=ENTITY_MAPPING_VERSION,
        )


def build_entity_mapping_section(
    injection_set: EntityInjectionSet,
    include_unknown: bool = True,
) -> PromptSection:
    """Convenience function to build entity mapping section."""
    injector = EntityInjector(include_unknown=include_unknown)
    return injector.inject(injection_set)


__all__ = [
    "EntityInjector",
    "build_entity_mapping_section",
    "ENTITY_MAPPING_SECTION_NAME",
    "ENTITY_MAPPING_VERSION",
]