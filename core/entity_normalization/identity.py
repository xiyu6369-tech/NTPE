"""RM-7.3 Entity Identity Resolution.

Manages canonical entity identities and their name forms.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.knowledge_evolution.models import EntityType as KEEntityType, PriorityLevel

from .models import (
    CanonicalEntity,
    EntityNameForms,
    EntityType,
    NameFormTranslation,
    NameFormType,
)


# Mapping from knowledge evolution entity types
KE_ENTITY_TYPE_MAP: Dict[KEEntityType, EntityType] = {
    KEEntityType.CHARACTER: EntityType.CHARACTER,
    KEEntityType.LOCATION: EntityType.LOCATION,
    KEEntityType.ORGANIZATION: EntityType.ORGANIZATION,
    KEEntityType.TERM: EntityType.TERM,
    KEEntityType.TITLE: EntityType.TERM,
    KEEntityType.ALIAS: EntityType.CHARACTER,
}

PRIORITY_ORDER: List[PriorityLevel] = [
    PriorityLevel.USER,
    PriorityLevel.RUNTIME,
    PriorityLevel.LEARNING,
    PriorityLevel.AUTO,
]


def map_ke_entity_type(ke_type: KEEntityType) -> EntityType:
    """Map KnowledgeEvolution EntityType to Normalization EntityType."""
    return KE_ENTITY_TYPE_MAP.get(ke_type, EntityType.TERM)


# Mapping from RM-7.2 EntityResolver string values (which differ from
# KEEntityType values: e.g. PLACE vs LOCATION, TERMINOLOGY vs TERM).
RESOLVER_TO_NORMALIZATION_TYPE: Dict[str, EntityType] = {
    "CHARACTER": EntityType.CHARACTER,
    "PLACE": EntityType.LOCATION,
    "LOCATION": EntityType.LOCATION,
    "ORGANIZATION": EntityType.ORGANIZATION,
    "TERMINOLOGY": EntityType.TERM,
    "TERM": EntityType.TERM,
}


def map_resolver_entity_type(resolver_type_str: str) -> EntityType:
    """Map an RM-7.2 EntityResolver entity type string to Normalization EntityType.

    The resolver emits string values that may differ from KEEntityType values
    (PLACE vs LOCATION, TERMINOLOGY vs TERM). This mapper handles both and
    falls back to TERM for unknown / UNKNOWN.
    """
    if not resolver_type_str:
        return EntityType.TERM
    upper = resolver_type_str.upper()
    if upper == "UNKNOWN":
        return EntityType.TERM
    return RESOLVER_TO_NORMALIZATION_TYPE.get(upper, EntityType.TERM)


def generate_entity_id(entity_type: EntityType, source_name: str) -> str:
    """Generate a stable entity ID from type and source name."""
    import hashlib
    content = f"{entity_type.value}:{source_name}"
    hash_suffix = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"{entity_type.value.lower()}_{hash_suffix}"


def build_canonical_entity(
    source_name: str,
    canonical_translation: str,
    entity_type: EntityType,
    name_forms: Optional[EntityNameForms] = None,
    entity_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> CanonicalEntity:
    """Build a CanonicalEntity with inferred name forms if not provided.

    For CHARACTER types, attempts to infer given/family name from Korean names.
    """
    if entity_id is None:
        entity_id = generate_entity_id(entity_type, source_name)

    if name_forms is None:
        name_forms = _infer_name_forms(source_name, canonical_translation, entity_type)

    return CanonicalEntity(
        entity_id=entity_id,
        entity_type=entity_type,
        source_name=source_name,
        canonical_translation=canonical_translation,
        name_forms=name_forms,
        metadata=metadata or {},
    )


def _infer_name_forms(
    source_name: str,
    canonical_translation: str,
    entity_type: EntityType
) -> EntityNameForms:
    """Infer name forms for Korean character names.

    Korean names typically: FamilyName + GivenName (2-3 syllables total)
    e.g., 정태의 -> 鄭泰義 (Family: 정/鄭, Given: 태의/泰義)

    For 2-character Korean names, we cannot reliably determine if it is a
    full name or a given name on its own. In that case, we set full_name
    only and leave given_name to be set by the linking resolver.
    """
    forms = {}

    if entity_type == EntityType.CHARACTER and len(source_name) >= 3:
        # Full Korean name (3+ chars): split into family + given
        family_source = source_name[0]
        given_source = source_name[1:]

        # Same split for translation (assuming same structure)
        if len(canonical_translation) >= 3:
            family_translation = canonical_translation[0]
            given_translation = canonical_translation[1:]

            forms["family_name"] = NameFormTranslation(
                source=family_source,
                translation=family_translation,
                form_type=NameFormType.FAMILY_NAME,
            )
            forms["given_name"] = NameFormTranslation(
                source=given_source,
                translation=given_translation,
                form_type=NameFormType.GIVEN_NAME,
            )
    elif entity_type == EntityType.CHARACTER and len(source_name) == 2:
        # 2-char names are ambiguous: could be a given name alone.
        # Do NOT auto-infer given_name (would produce broken 1-char names).
        # The resolver will link these as surface forms of a full entity.

        # Check if it looks like a known full name pattern (1 family + 1 given)
        # e.g., "金泰" style. Set given_name only if translation is also 2 chars.
        if len(canonical_translation) == 2:
            forms["given_name"] = NameFormTranslation(
                source=source_name,
                translation=canonical_translation,
                form_type=NameFormType.GIVEN_NAME,
            )

    # Full name is always the source
    forms["full_name"] = NameFormTranslation(
        source=source_name,
        translation=canonical_translation,
        form_type=NameFormType.FULL_NAME,
    )

    return EntityNameForms(**forms)


class EntityIdentityRegistry:
    """Registry of canonical entities with identity management."""

    def __init__(self):
        self._entities: Dict[str, CanonicalEntity] = {}  # entity_id -> CanonicalEntity
        self._source_to_id: Dict[str, str] = {}  # source_name -> entity_id

    def register(self, entity: CanonicalEntity) -> None:
        """Register a canonical entity."""
        self._entities[entity.entity_id] = entity
        # Map all known surface forms to this entity
        for form in entity.name_forms.get_all_forms():
            self._source_to_id[form.source] = entity.entity_id
        # Also map the canonical source name
        self._source_to_id[entity.source_name] = entity.entity_id

    def get_by_id(self, entity_id: str) -> Optional[CanonicalEntity]:
        """Get entity by ID."""
        return self._entities.get(entity_id)

    def get_by_source(self, source: str) -> Optional[CanonicalEntity]:
        """Get entity by any known surface form."""
        entity_id = self._source_to_id.get(source)
        if entity_id:
            return self._entities.get(entity_id)
        return None

    def resolve_source(self, source: str) -> Optional[CanonicalEntity]:
        """Resolve a source text to its canonical entity.

        Handles spacing variants: '정태의', '정 태의' -> same entity
        """
        # Direct match
        entity = self.get_by_source(source)
        if entity:
            return entity

        # Try normalized (remove spaces)
        normalized = source.replace(" ", "")
        entity = self.get_by_source(normalized)
        if entity:
            return entity

        return None

    def get_all_entities(self) -> List[CanonicalEntity]:
        """Get all registered entities."""
        return list(self._entities.values())

    def get_entities_by_type(self, entity_type: EntityType) -> List[CanonicalEntity]:
        """Get all entities of a specific type."""
        return [e for e in self._entities.values() if e.entity_type == entity_type]

    def update_name_forms(self, entity_id: str, name_forms: EntityNameForms) -> bool:
        """Update name forms for an entity."""
        entity = self._entities.get(entity_id)
        if not entity:
            return False

        # Re-register with new forms (immutable, so create new)
        new_entity = CanonicalEntity(
            entity_id=entity.entity_id,
            entity_type=entity.entity_type,
            source_name=entity.source_name,
            canonical_translation=entity.canonical_translation,
            name_forms=name_forms,
            metadata=entity.metadata,
            created_at=entity.created_at,
            updated_at=utc_now_iso(),
            version=entity.version,
        )
        self.register(new_entity)
        return True

    def clear(self) -> None:
        """Clear all entities."""
        self._entities.clear()
        self._source_to_id.clear()


# Global registry instance
_identity_registry = EntityIdentityRegistry()


def get_identity_registry() -> EntityIdentityRegistry:
    """Get the global identity registry."""
    return _identity_registry


def register_entity(entity: CanonicalEntity) -> None:
    """Register an entity in the global registry."""
    _identity_registry.register(entity)


def resolve_entity(source: str) -> Optional[CanonicalEntity]:
    """Resolve a source text to its canonical entity via global registry."""
    return _identity_registry.resolve_source(source)


def utc_now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "EntityIdentityRegistry",
    "build_canonical_entity",
    "generate_entity_id",
    "map_ke_entity_type",
    "map_resolver_entity_type",
    "get_identity_registry",
    "register_entity",
    "resolve_entity",
    "KE_ENTITY_TYPE_MAP",
    "RESOLVER_TO_NORMALIZATION_TYPE",
    "PRIORITY_ORDER",
]