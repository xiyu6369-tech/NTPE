"""P0 Stage 5 Batch 5.3 — Series Entity Registry.

Persistent Series-level canonical entity registry with namespace isolation.
CRUD, typed queries, hydration (READ-ONLY), promotion (MANUAL gate).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .models import (
    SeriesEntityRecord,
    EntityPromotionRecord,
    ConflictRecord,
    AddResult,
    HydrationReport,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    EntityType,
    RecordLifecycle,
    PromotionAction,
    utc_now_iso,
    compute_series_entity_id,
)
from .persistence import (
    get_series_dir,
    get_series_entity_registry_path,
    save_series_entity_registry,
    load_series_entity_registry,
    verify_series_entity_registry_integrity,
    create_empty_series_entity_registry,
)
from .validation import (
    validate_series_entity_record,
    compute_series_entity_registry_fingerprint,
    SeriesEntityValidationError,
)


@dataclass(frozen=True)
class RegistryLoadResult:
    entities: Mapping[str, SeriesEntityRecord]
    promotions: Tuple[EntityPromotionRecord, ...]
    registry_hash: str


class SeriesEntityRegistry:
    """
    Series-scoped canonical entity registry.

    Namespace isolation: All operations require explicit series_id.
    Entity IDs: sentity_{sha256(series_id|source|type)[:16]} (SE-3 typed).
    Integration: READ-ONLY hydration via EntityResolver.user_overrides (SE-4).
    Promotion: MANUAL approval gate only (D-07 frozen).
    """

    def __init__(
        self,
        series_id: str,
        output_root: Path,
        *,
        existing_entities: Optional[Mapping[str, SeriesEntityRecord]] = None,
        existing_promotions: Optional[Tuple[EntityPromotionRecord, ...]] = None,
    ) -> None:
        """
        Initialize registry for a specific series.

        Args:
            series_id: Series identity (namespace)
            output_root: Root output directory
            existing_entities: Pre-loaded entities (for testing/incremental)
            existing_promotions: Pre-loaded promotions (for testing/incremental)
        """
        if not series_id:
            raise SeriesEntityValidationError("series_id cannot be empty")

        self.series_id = series_id
        self.output_root = output_root
        self.series_dir = get_series_dir(output_root, series_id)
        self.registry_path = get_series_entity_registry_path(self.series_dir, series_id)

        self._entities: Dict[str, SeriesEntityRecord] = dict(existing_entities) if existing_entities else {}
        self._promotions: List[EntityPromotionRecord] = list(existing_promotions) if existing_promotions else []
        self._conflicts: Dict[str, ConflictRecord] = {}

    @classmethod
    def load(cls, series_id: str, output_root: Path) -> "SeriesEntityRegistry":
        """Load registry from disk (fail-closed)."""
        registry = cls(series_id, output_root)
        entities, promotions, loaded_series_id = load_series_entity_registry(registry.registry_path)

        if loaded_series_id != series_id:
            raise SeriesEntityValidationError(
                f"Loaded series_id mismatch: expected {series_id}, got {loaded_series_id}"
            )

        registry._entities = dict(entities)
        registry._promotions = list(promotions)
        registry._conflicts = {}
        return registry

    @classmethod
    def create_new(cls, series_id: str, output_root: Path) -> "SeriesEntityRegistry":
        """Create a new empty registry for a series."""
        registry = cls(series_id, output_root)
        registry._entities = {}
        registry._promotions = []
        registry._conflicts = {}
        return registry

    # --- Core Properties ---

    @property
    def entities(self) -> Mapping[str, SeriesEntityRecord]:
        """All entities (read-only view)."""
        return self._entities

    @property
    def promotions(self) -> Tuple[EntityPromotionRecord, ...]:
        """All promotion records (read-only view)."""
        return tuple(self._promotions)

    def get_registry_hash(self) -> str:
        """Compute SHA-256 fingerprint of current registry state."""
        payload = {
            "schema_name": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "series_id": self.series_id,
            "entities": [record.to_dict() for record in self._entities.values()],
            "promotions": [record.to_dict() for record in self._promotions],
        }
        return compute_series_entity_registry_fingerprint(payload)

    def validate_integrity(self) -> bool:
        """Verify SHA-256 fingerprint matches stored data."""
        if not self.registry_path.exists():
            return False
        return verify_series_entity_registry_integrity(self.registry_path, self.get_registry_hash())

    # --- CRUD Operations ---

    def register(
        self,
        source_name: str,
        entity_type: EntityType,
        canonical_target: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        approved_by: str = "user",
        source_books: Optional[Tuple[str, ...]] = None,
    ) -> AddResult:
        """
        Add or merge a canonical entity.

        SE-3: Typed query - entity_type required.
        Conflict detection: SAME value → NO-OP, DIFFERENT → CONFLICT.
        """
        source_name = source_name.strip()
        if not source_name:
            raise SeriesEntityValidationError("source_name cannot be empty")

        if not canonical_target:
            raise SeriesEntityValidationError("canonical_target cannot be empty")

        # Accept both EntityType enum and string (for test compatibility)
        if isinstance(entity_type, str):
            try:
                entity_type = EntityType(entity_type.upper())
            except ValueError:
                raise SeriesEntityValidationError(f"Invalid entity_type: {entity_type}")

        # Validate entity_type is from RM-7.2 set (SE-1 frozen)
        if entity_type not in (EntityType.CHARACTER, EntityType.PLACE, EntityType.ORGANIZATION,
                                EntityType.TERMINOLOGY, EntityType.UNKNOWN):
            raise SeriesEntityValidationError(f"Invalid entity_type: {entity_type.value}")

        series_entity_id = compute_series_entity_id(self.series_id, source_name, entity_type.value)

        existing = self._entities.get(series_entity_id)

        now = utc_now_iso()
        meta = dict(metadata) if metadata else {}
        if source_books:
            meta.setdefault("source_books", list(source_books))
            meta.setdefault("book_coverage", len(source_books))

        if existing is None:
            # CREATE new
            record = SeriesEntityRecord(
                series_entity_id=series_entity_id,
                series_id=self.series_id,
                source_name=source_name,
                entity_type=entity_type,
                canonical_target=canonical_target,
                version=1,
                lifecycle=RecordLifecycle.CREATED,
                metadata=meta,
                approved_at=now,
                approved_by=approved_by,
                created_at=now,
            )

            report = validate_series_entity_record(record)
            if not report.valid:
                raise SeriesEntityValidationError(f"Invalid record: {'; '.join(report.errors)}")

            self._entities[series_entity_id] = record
            return AddResult(
                disposition="accepted",
                record=record,
                message="New canonical entity added",
            )

        if existing.canonical_target == canonical_target:
            # NO-OP: same value already exists
            return AddResult(
                disposition="no_op",
                record=existing,
                message="Same canonical target already exists",
            )

        # CONFLICT: different canonical target
        conflict = ConflictRecord(
            conflict_id=hashlib.sha256(
                f"{series_entity_id}|{entity_type.value}|{canonical_target}|{existing.canonical_target}".encode()
            ).hexdigest()[:12],
            series_entity_id=series_entity_id,
            entity_type=entity_type,
            existing_target=existing.canonical_target,
            proposed_target=canonical_target,
            created_at=now,
        )

        return AddResult(
            disposition="conflict",
            record=existing,
            conflict=conflict,
            message="Conflicting canonical target requires MANUAL resolution",
        )

    def get(self, series_entity_id: str) -> Optional[SeriesEntityRecord]:
        """Get entity by namespace-isolated ID."""
        return self._entities.get(series_entity_id)

    def get_by_source(self, source_name: str, entity_type: EntityType | str) -> Optional[SeriesEntityRecord]:
        """
        Get entity by source name + type (SE-3: typed query required).

        Args:
            source_name: Korean source name
            entity_type: Entity type (REQUIRED - no untyped lookup)

        Returns:
            SeriesEntityRecord or None
        """
        if isinstance(entity_type, str):
            entity_type = EntityType(entity_type.upper())

        series_entity_id = compute_series_entity_id(self.series_id, source_name, entity_type.value)
        return self._entities.get(series_entity_id)

    def get_all(self) -> Tuple[SeriesEntityRecord, ...]:
        """Get all entities sorted by ID."""
        return tuple(sorted(self._entities.values(), key=lambda r: r.series_entity_id))

    def get_by_type(self, entity_type: EntityType | str) -> Tuple[SeriesEntityRecord, ...]:
        """Get all entities of a specific type."""
        if isinstance(entity_type, str):
            entity_type = EntityType(entity_type.upper())
        return tuple(
            r for r in self._entities.values()
            if r.entity_type == entity_type
        )

    def update_target(
        self,
        series_entity_id: str,
        new_target: str,
        approved_by: str = "user",
    ) -> AddResult:
        """
        Supersede canonical target (SE-5: per-record versioning).

        Creates new version with incremented version number.
        """
        if not new_target:
            raise SeriesEntityValidationError("new_target cannot be empty")

        existing = self._entities.get(series_entity_id)
        if existing is None:
            raise SeriesEntityValidationError(f"Entity not found: {series_entity_id}")

        if existing.canonical_target == new_target:
            return AddResult(
                disposition="no_op",
                record=existing,
                message="Target already matches",
            )

        # Supersede: create new version
        updated = existing.with_superseded_target(new_target, approved_by)
        self._entities[series_entity_id] = updated

        return AddResult(
            disposition="accepted",
            record=updated,
            message=f"Canonical target superseded (v{updated.version})",
        )

    def archive(self) -> None:
        """Archive all entities (read-only mode)."""
        for entity_id, record in self._entities.items():
            if record.lifecycle != RecordLifecycle.ARCHIVED:
                self._entities[entity_id] = record.with_lifecycle(RecordLifecycle.ARCHIVED)

    # --- Persistence ---

    def save(self) -> Mapping[str, Any]:
        """Save registry to disk."""
        return save_series_entity_registry(
            self.series_id,
            self._entities,
            tuple(self._promotions),
            self.registry_path,
        )

    # --- Hydration (Series → Book) READ-ONLY ---

    def hydrate_resolver(
        self,
        book_identity: str,
    ) -> Tuple[Dict[str, str], HydrationReport]:
        """
        Produce user_overrides dict for EntityResolver hydration.

        READ-ONLY projection — does not mutate Series state.
        Returns Dict[source_name, canonical_target] compatible with
        EntityResolver(user_overrides=...).

        SE-4: Uses EXISTING user_overrides extension point only.
        """
        hydration_source = f"series:{self.series_id}:{self.get_registry_hash()}"
        overrides: Dict[str, str] = {}
        hydrated = 0
        skipped = 0
        conflicts = []

        for record in self._entities.values():
            if record.lifecycle == RecordLifecycle.ARCHIVED:
                skipped += 1
                continue

            source = record.source_name
            if source in overrides:
                # This shouldn't happen due to namespace isolation, but handle gracefully
                if overrides[source] != record.canonical_target:
                    conflicts.append(f"HYDRATION CONFLICT: {source} -> {overrides[source]} vs {record.canonical_target}")
                skipped += 1
                continue

            overrides[source] = record.canonical_target
            hydrated += 1

        report = HydrationReport(
            series_id=self.series_id,
            book_identity=book_identity,
            hydrated_count=hydrated,
            skipped_count=skipped,
            conflict_count=len(conflicts),
            hydration_source=hydration_source,
            conflicts=tuple(conflicts),
        )

        return overrides, report

    # --- Promotion (Book → Series) MANUAL GATE ---

    def promote_from_resolver(
        self,
        resolver_user_overrides: Mapping[str, str],
        book_identity: str,
        *,
        approval_gate: bool = True,
    ) -> Tuple[AddResult, ...]:
        """
        Promote USER overrides from EntityResolver to SeriesEntityRegistry.

        D-07 FROZEN: MANUAL approval gate required.
        Only USER_OVERRIDE source_level promoted.
        LEARNING data is NOT promoted.

        Args:
            resolver_user_overrides: The user_overrides dict from EntityResolver
            book_identity: Book identity for provenance
            approval_gate: MUST be True (D-07 frozen)

        Returns:
            Tuple of AddResult for each promoted entity

        Raises:
            SeriesEntityValidationError: If approval_gate is False
        """
        if approval_gate is False:
            raise SeriesEntityValidationError(
                "Entity promotion requires MANUAL approval gate (D-07 frozen). "
                "Auto-promotion is not permitted."
            )

        results = []

        for source_name, target in resolver_user_overrides.items():
            if not target or target == "(No predefined translation)":
                continue

            # Infer entity_type - default to CHARACTER for names, TERMINOLOGY for terms
            # This is a simplification; in practice caller should provide entity_type mapping
            entity_type = self._infer_entity_type(source_name)

            # Check if this entity already exists in registry
            existing = self.get_by_source(source_name, entity_type)

            promotion_id = hashlib.sha256(
                f"{self.series_id}|{book_identity}|{source_name}|{utc_now_iso()}".encode()
            ).hexdigest()[:12]

            if existing is None:
                # CREATE new
                result = self.register(
                    source_name=source_name,
                    entity_type=entity_type,
                    canonical_target=target,
                    approved_by="series_promotion",
                    source_books=(book_identity,),
                )

                promotion = EntityPromotionRecord(
                    promotion_id=promotion_id,
                    series_id=self.series_id,
                    book_identity=book_identity,
                    source_name=source_name,
                    entity_type=entity_type,
                    previous_target=None,
                    new_target=target,
                    action=PromotionAction.CREATED,
                    resolved_by="user",
                    resolved_at=utc_now_iso(),
                    source_level="USER_OVERRIDE",
                )
                self._promotions.append(promotion)

                results.append(AddResult(
                    disposition=result.disposition,
                    record=result.record,
                    message=f"Promoted from book {book_identity}",
                ))

            elif existing.canonical_target == target:
                # NO-OP: same value
                promotion = EntityPromotionRecord(
                    promotion_id=promotion_id,
                    series_id=self.series_id,
                    book_identity=book_identity,
                    source_name=source_name,
                    entity_type=entity_type,
                    previous_target=existing.canonical_target,
                    new_target=target,
                    action=PromotionAction.NO_OP,
                    resolved_by="system",
                    resolved_at=utc_now_iso(),
                    source_level="USER_OVERRIDE",
                )
                self._promotions.append(promotion)

                results.append(AddResult(
                    disposition="no_op",
                    record=existing,
                    message="Same canonical target already exists in series",
                ))

            else:
                # CONFLICT: different value
                conflict = ConflictRecord(
                    conflict_id=hashlib.sha256(
                        f"{self.series_id}|{source_name}|{entity_type.value}|{target}|{existing.canonical_target}".encode()
                    ).hexdigest()[:12],
                    series_entity_id=existing.series_entity_id,
                    entity_type=entity_type,
                    existing_target=existing.canonical_target,
                    proposed_target=target,
                    created_at=utc_now_iso(),
                )
                # Store conflict for later resolution
                self._conflicts[conflict.conflict_id] = conflict

                promotion = EntityPromotionRecord(
                    promotion_id=promotion_id,
                    series_id=self.series_id,
                    book_identity=book_identity,
                    source_name=source_name,
                    entity_type=entity_type,
                    previous_target=existing.canonical_target,
                    new_target=target,
                    action=PromotionAction.CONFLICT,
                    resolved_by=None,  # Requires manual resolution
                    resolved_at=utc_now_iso(),
                    source_level="USER_OVERRIDE",
                )
                self._promotions.append(promotion)

                results.append(AddResult(
                    disposition="conflict",
                    record=existing,
                    conflict=conflict,
                    message=f"CONFLICT: Series has '{existing.canonical_target}', book proposes '{target}'",
                ))

        return tuple(results)

    def resolve_promotion_conflict(
        self,
        conflict_id: str,
        resolution: str,  # "book_wins" | "series_wins" | "manual"
        resolved_by: str,
        manual_value: Optional[str] = None,
    ) -> AddResult:
        """
        Resolve a promotion conflict (MANUAL resolution).

        Args:
            conflict_id: The conflict ID to resolve
            resolution: "book_wins" (use proposed), "series_wins" (keep existing), "manual" (custom value)
            resolved_by: Who resolved the conflict
            manual_value: Custom value if resolution="manual"

        Returns:
            AddResult with resolved record
        """
        conflict = self._conflicts.get(conflict_id)
        if conflict is None:
            raise SeriesEntityValidationError(f"Conflict not found: {conflict_id}")

        if conflict.resolution is not None:
            raise SeriesEntityValidationError(f"Conflict {conflict_id} already resolved")

        record = self._entities.get(conflict.series_entity_id)
        if record is None:
            raise SeriesEntityValidationError(f"Entity not found for conflict: {conflict.series_entity_id}")

        if resolution == "book_wins":
            new_target = conflict.proposed_target
        elif resolution == "series_wins":
            new_target = conflict.existing_target
        elif resolution == "manual":
            if manual_value is None:
                raise SeriesEntityValidationError("manual_value required for manual resolution")
            new_target = manual_value
        else:
            raise SeriesEntityValidationError(f"Invalid resolution: {resolution}")

        # Update record (creates new version)
        updated = record.with_superseded_target(new_target, resolved_by)
        self._entities[conflict.series_entity_id] = updated

        # Update conflict record in storage
        resolved_conflict = ConflictRecord(
            conflict_id=conflict.conflict_id,
            series_entity_id=conflict.series_entity_id,
            entity_type=conflict.entity_type,
            existing_target=conflict.existing_target,
            proposed_target=conflict.proposed_target,
            created_at=conflict.created_at,
            resolution=resolution,
            resolved_at=utc_now_iso(),
            resolved_by=resolved_by,
        )
        self._conflicts[conflict_id] = resolved_conflict

        return AddResult(
            disposition="accepted",
            record=updated,
            conflict=resolved_conflict,
            message=f"Conflict resolved: {resolution}",
        )

    def _infer_entity_type(self, source_name: str) -> EntityType:
        """Infer entity type from source name (simplified heuristic)."""
        # Default to CHARACTER for Korean names
        # In practice, this should be provided by caller
        return EntityType.CHARACTER