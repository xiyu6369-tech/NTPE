"""RM-7.1 Entity Consistency Runtime — public API.

Detect → Report → Review only.  Never mutates translations, knowledge,
or glossaries.  Read-only scanner + checker + reporter.
"""

from .checker import ConsistencyChecker
from .models import (
    ConsistencyReport,
    EntityCategory,
    EntityMatch,
    EntityMismatch,
    ReportSeverity,
)
from .report import ConsistencyReporter
from .scanner import EntityScanner
from .variants import (
    normalize_for_comparison,
    are_variants_equal,
    find_normalized,
    find_all_normalized,
)
from .matching_policy import (
    FormAwareMatchingPolicy,
    MatchResult,
    FormMatchSpec,
    NameFormType,
    create_matching_policy,
    create_matching_policy_from_entity,
)

__all__ = [
    "EntityCategory",
    "EntityMatch",
    "EntityMismatch",
    "ConsistencyReport",
    "ReportSeverity",
    "EntityScanner",
    "ConsistencyChecker",
    "ConsistencyReporter",
    "normalize_for_comparison",
    "are_variants_equal",
    "find_normalized",
    "find_all_normalized",
    "FormAwareMatchingPolicy",
    "MatchResult",
    "FormMatchSpec",
    "NameFormType",
    "create_matching_policy",
    "create_matching_policy_from_entity",
]