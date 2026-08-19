"""P0 Stage 5 Batch 5.3 — EntityResolver Integration.

Integration via EXISTING RM-7.2 user_overrides extension point ONLY.
NO modifications to EntityResolver core.

SE-4 FROZEN: Uses existing EntityResolver(user_overrides=...) parameter.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Tuple

from .registry import SeriesEntityRegistry
from .models import HydrationReport


def hydrate_resolver_from_series(
    series_registry: SeriesEntityRegistry,
    book_identity: str,
) -> Tuple[Dict[str, str], HydrationReport]:
    """
    Hydrate EntityResolver with Series entity overrides.

    READ-ONLY projection: SeriesEntityRegistry → user_overrides dict.
    Compatible with EXISTING EntityResolver extension point:
        EntityResolver(user_overrides=overrides, ...)

    SE-4 FROZEN: Uses EXISTING user_overrides parameter only.
    NO modifications to EntityResolver core.
    Precedence preserved: USER/SERIES > RUNTIME > LEARNING > AUTO

    Args:
        series_registry: SeriesEntityRegistry for the series
        book_identity: Book identity for provenance

    Returns:
        Tuple of (user_overrides_dict, HydrationReport)
    """
    return series_registry.hydrate_resolver(book_identity)


def create_resolver_with_series_hydration(
    series_registry: SeriesEntityRegistry,
    book_identity: str,
    runtime: Any = None,
    learning_data: Dict[str, str] = None,  # type: ignore[assignment]
) -> Any:
    """
    Factory to create EntityResolver with Series hydration.

    Uses existing EntityResolver extension point:
        EntityResolver(user_overrides=..., runtime=..., learning_data=...)

    SE-4 FROZEN: Does NOT modify EntityResolver class.
    Caller is responsible for importing EntityResolver and using this factory
    or manually constructing the resolver.

    Example:
        from core.entity_resolver import EntityResolver
        from core.knowledge_runtime import MergedRuntime

        runtime = MergedRuntime(...)
        overrides, report = hydrate_resolver_from_series(registry, book_id)
        resolver = EntityResolver(
            runtime=runtime,
            user_overrides=overrides,
            learning_data=learning_data or {},
        )

    Args:
        series_registry: SeriesEntityRegistry for the series
        book_identity: Book identity
        runtime: Optional MergedRuntime
        learning_data: Optional learning data

    Returns:
        Configured EntityResolver instance
    """
    # This is a helper - actual EntityResolver import done by caller
    # to avoid circular imports and respect frozen boundary
    overrides, _ = series_registry.hydrate_resolver(book_identity)

    # Import here to avoid circular dependency and respect frozen boundary
    from core.entity_resolver import EntityResolver

    return EntityResolver(
        runtime=runtime,
        user_overrides=overrides,
        learning_data=learning_data or {},
    )


__all__ = [
    "hydrate_resolver_from_series",
    "create_resolver_with_series_hydration",
]