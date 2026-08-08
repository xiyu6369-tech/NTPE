"""RM-7.3 Entity Normalization Package.

Entity Identity + Surface Form + Context Rule architecture for novel translation.
"""

from .models import (
    EntityType,
    NameFormType,
    ConflictSeverity,
    ResolutionSource,
    NameFormTranslation,
    EntityNameForms,
    CanonicalEntity,
    ConflictRecord,
    NormalizationContext,
    NormalizedEntity,
    NormalizationResult,
)

from .identity import (
    EntityIdentityRegistry,
    build_canonical_entity,
    generate_entity_id,
    map_ke_entity_type,
    get_identity_registry,
    register_entity,
    resolve_entity,
    KE_ENTITY_TYPE_MAP,
    PRIORITY_ORDER,
)

from .name_form import (
    classify_name_form,
    resolve_name_form,
    build_normalized_entity,
    extract_context_from_text,
    FORMAL_SUFFIXES,
    INTIMATE_SUFFIXES,
    RELATIONSHIP_TERMS,
)

from .conflict import (
    ConflictDetector,
    ConflictResolver,
    ConflictCandidate,
    build_candidates_from_sources,
)

from .normalizer import (
    EntityNormalizer,
    create_normalizer,
)

from .resolver import (
    NormalizationResolver,
    create_normalization_resolver,
)

from .report import (
    NormalizationReport,
    NormalizationReporter,
    build_prompt_section,
    build_compact_prompt_section,
)

__version__ = "rm-7.3.0"

__all__ = [
    # Models
    "EntityType",
    "NameFormType",
    "ConflictSeverity",
    "ResolutionSource",
    "NameFormTranslation",
    "EntityNameForms",
    "CanonicalEntity",
    "ConflictRecord",
    "NormalizationContext",
    "NormalizedEntity",
    "NormalizationResult",
    # Identity
    "EntityIdentityRegistry",
    "build_canonical_entity",
    "generate_entity_id",
    "map_ke_entity_type",
    "get_identity_registry",
    "register_entity",
    "resolve_entity",
    "KE_ENTITY_TYPE_MAP",
    "PRIORITY_ORDER",
    # Name Form
    "classify_name_form",
    "resolve_name_form",
    "build_normalized_entity",
    "extract_context_from_text",
    "FORMAL_SUFFIXES",
    "INTIMATE_SUFFIXES",
    "RELATIONSHIP_TERMS",
    # Conflict
    "ConflictDetector",
    "ConflictResolver",
    "ConflictCandidate",
    "build_candidates_from_sources",
    # Normalizer
    "EntityNormalizer",
    "create_normalizer",
    # Resolver
    "NormalizationResolver",
    "create_normalization_resolver",
    # Report
    "NormalizationReport",
    "NormalizationReporter",
    "build_prompt_section",
    "build_compact_prompt_section",
]