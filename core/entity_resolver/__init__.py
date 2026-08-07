"""RM-7.2 Entity Resolver - Pre-translation entity resolution.

This module provides entity extraction, resolution, and injection
for the translation pipeline. It sits between Merged Runtime and
Prompt Builder to provide LLM with predefined entity translations
before translation begins.

Architecture:
    Knowledge Runtime
          │
          ▼
    Merged Runtime
          │
          ▼
    Entity Resolver      ← RM-7.2 (this module)
          │
          ▼
    Prompt Builder
          │
          ▼
    Translation Engine

Components:
    - models.py: ResolvedEntity, EntityInjectionSet, InjectionSource, ExtractedEntity
    - extractor.py: Extract Korean entities from chunks
    - resolver.py: Resolve using USER > RUNTIME > LEARNING > AUTO hierarchy
    - injector.py: Inject as Prompt 'Entity Mapping' section

Usage:
    from core.entity_resolver import (
        EntityExtractor,
        EntityResolver,
        EntityInjector,
        build_known_entities_from_runtime,
    )

    # 1. Extract entities from chunk
    extractor = EntityExtractor(known_entities=build_known_entities_from_runtime(runtime))
    extracted = extractor.extract(chunk_text)

    # 2. Resolve with priority hierarchy
    resolver = EntityResolver(runtime=runtime, user_overrides=user_dict)
    injection_set = resolver.resolve(extracted)

    # 3. Inject into prompt
    injector = EntityInjector()
    entity_section = injector.inject(injection_set)
"""

from __future__ import annotations

from .models import (
    EntityType,
    InjectionSource,
    ResolvedEntity,
    EntityInjectionSet,
    ExtractedEntity,
)
from .extractor import (
    EntityExtractor,
    build_known_entities_from_runtime,
    KOREAN_NAME_PATTERN,
)
from .resolver import (
    EntityResolver,
    build_user_overrides_from_config,
    build_learning_data_from_history,
    UNKNOWN_TRANSLATION,
)
from .injector import (
    EntityInjector,
    build_entity_mapping_section,
    ENTITY_MAPPING_SECTION_NAME,
    ENTITY_MAPPING_VERSION,
)

__all__ = [
    # Models
    "EntityType",
    "InjectionSource",
    "ResolvedEntity",
    "EntityInjectionSet",
    "ExtractedEntity",
    # Extractor
    "EntityExtractor",
    "build_known_entities_from_runtime",
    "KOREAN_NAME_PATTERN",
    # Resolver
    "EntityResolver",
    "build_user_overrides_from_config",
    "build_learning_data_from_history",
    "UNKNOWN_TRANSLATION",
    # Injector
    "EntityInjector",
    "build_entity_mapping_section",
    "ENTITY_MAPPING_SECTION_NAME",
    "ENTITY_MAPPING_VERSION",
]

__version__ = "rm-7.2.0"