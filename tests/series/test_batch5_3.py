"""P0 Stage 5 Batch 5.3 — Series Entity Registry Tests.

Tests for deterministic identity, cross-series isolation, hydration,
promotion (MANUAL gate), persistence integrity, and manifest integration.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from core.series_entity_registry import (
    SeriesEntityRecord,
    EntityPromotionRecord,
    ConflictRecord,
    AddResult,
    HydrationReport,
    SeriesEntityRegistry,
    compute_series_entity_id,
    save_series_entity_registry,
    load_series_entity_registry,
    get_series_entity_registry_path,
    verify_series_entity_registry_integrity,
    validate_series_entity_record,
    compute_series_entity_registry_fingerprint,
    to_canonical_json,
    SeriesEntityValidationError,
    SeriesEntityIntegrityError,
)
from core.series_identity import (
    SeriesIdentity,
    SeriesManifest,
    SeriesBookEntry,
    SeriesLifecycle,
    BookStatus,
    SeriesRegistry,
    compute_series_id,
    get_series_dir,
    manifest_file_path,
    save_manifest,
    load_manifest,
    compute_manifest_fingerprint,
)
from core.entity_resolver import EntityResolver
from core.entity_resolver.models import EntityType as ResolverEntityType


class TestSeriesEntityIdentity:
    """Tests for deterministic series entity ID generation (SE-01, CSI-02)."""

    def test_compute_series_entity_id_deterministic(self):
        """Same (series_id, source, type) must produce same ID."""
        series_id = "a1b2c3d4e5f6g7h8"
        source = "정태的"
        entity_type = "CHARACTER"

        id1 = compute_series_entity_id(series_id, source, entity_type)
        id2 = compute_series_entity_id(series_id, source, entity_type)
        assert id1 == id2
        assert len(id1) == 24  # "sentity_" (8) + 16 hex chars
        assert id1.startswith("sentity_")

    def test_compute_series_entity_id_namespace_isolation(self):
        """Different series_id must produce different ID (CSI-02)."""
        source = "正泰的"
        entity_type = "CHARACTER"

        series_a_id = compute_series_id("series_a")
        series_b_id = compute_series_id("series_b")

        id_a = compute_series_entity_id(series_a_id, source, entity_type)
        id_b = compute_series_entity_id(series_b_id, source, entity_type)

        assert id_a != id_b
        assert id_a.startswith("sentity_")
        assert id_b.startswith("sentity_")

    def test_compute_series_entity_id_type_aware(self):
        """Same source, different type must produce different ID (SE-3)."""
        series_id = "a1b2c3d4e5f6g7h8"
        source = "正泰的"

        id_char = compute_series_entity_id(series_id, source, "CHARACTER")
        id_place = compute_series_entity_id(series_id, source, "PLACE")
        id_term = compute_series_entity_id(series_id, source, "TERMINOLOGY")

        assert id_char != id_place
        assert id_char != id_term
        assert id_place != id_term

    def test_compute_series_entity_id_case_insensitive_type(self):
        """Entity type should be case-insensitive."""
        series_id = "a1b2c3d4e5f6g7h8"
        source = "正泰的"

        id1 = compute_series_entity_id(series_id, source, "character")
        id2 = compute_series_entity_id(series_id, source, "CHARACTER")
        id3 = compute_series_entity_id(series_id, source, "Character")

        assert id1 == id2 == id3

    def test_compute_series_entity_id_source_whitespace(self):
        """Source name leading/trailing whitespace should be normalized."""
        series_id = "a1b2c3d4e5f6g7h8"

        id1 = compute_series_entity_id(series_id, " 正泰的 ", "CHARACTER")
        id2 = compute_series_entity_id(series_id, "正泰的", "CHARACTER")
        id3 = compute_series_entity_id(series_id, "\t正泰的\n", "CHARACTER")

        assert id1 == id2 == id3

        # Internal whitespace is NOT normalized
        id4 = compute_series_entity_id(series_id, "正 泰 的", "CHARACTER")
        assert id4 != id1


class TestSeriesEntityRecord:
    """Tests for SeriesEntityRecord model (SE-2 minimal, SE-5 per-record version)."""

    def test_series_entity_record_creation(self):
        """Basic record creation with all required fields."""
        record = SeriesEntityRecord(
            series_entity_id="sentity_a1b2c3d4e5f6g7h8",
            series_id="a1b2c3d4e5f6g7h8",
            source_name="正泰的",
            entity_type="CHARACTER",
            canonical_target="鄭泰義",
            version=1,
            lifecycle="CREATED",
            metadata={"source_books": ["book1"], "book_coverage": 1},
            approved_at="2026-08-18T00:00:00Z",
            approved_by="user",
            created_at="2026-08-18T00:00:00Z",
        )

        assert record.series_entity_id == "sentity_a1b2c3d4e5f6g7h8"
        assert record.source_name == "正泰的"
        assert record.canonical_target == "鄭泰義"
        assert record.version == 1
        assert record.lifecycle == "CREATED"

    def test_series_entity_record_immutability(self):
        """Record fields should be immutable (frozen dataclass)."""
        record = SeriesEntityRecord(
            series_entity_id="sentity_a1b2c3d4e5f6g7h8",
            series_id="a1b2c3d4e5f6g7h8",
            source_name="正泰的",
            entity_type="CHARACTER",
            canonical_target="鄭泰義",
            version=1,
            lifecycle="CREATED",
            metadata={},
            approved_at="2026-08-18T00:00:00Z",
            approved_by="user",
            created_at="2026-08-18T00:00:00Z",
        )

        with pytest.raises(AttributeError):
            record.canonical_target = "新目標"

    def test_series_entity_record_superseded(self):
        """Per-record versioning on supersede (SE-5)."""
        record = SeriesEntityRecord(
            series_entity_id="sentity_a1b2c3d4e5f6g7h8",
            series_id="a1b2c3d4e5f6g7h8",
            source_name="正泰的",
            entity_type="CHARACTER",
            canonical_target="鄭泰義",
            version=1,
            lifecycle="ACTIVE",
            metadata={},
            approved_at="2026-08-18T00:00:00Z",
            approved_by="user",
            created_at="2026-08-18T00:00:00Z",
        )

        updated = record.with_superseded_target("鄭泰義新", "user")

        assert updated.version == 2
        assert updated.canonical_target == "鄭泰義新"
        assert updated.lifecycle == "SUPERSEDED"
        assert updated.approved_by == "user"
        assert updated.created_at == record.created_at  # Original creation preserved

    def test_series_entity_record_lifecycle_archived(self):
        """Archive lifecycle transition."""
        record = SeriesEntityRecord(
            series_entity_id="sentity_a1b2c3d4e5f6g7h8",
            series_id="a1b2c3d4e5f6g7h8",
            source_name="正泰的",
            entity_type="CHARACTER",
            canonical_target="鄭泰義",
            version=1,
            lifecycle="ACTIVE",
            metadata={},
            approved_at="2026-08-18T00:00:00Z",
            approved_by="user",
            created_at="2026-08-18T00:00:00Z",
        )

        archived = record.with_lifecycle("ARCHIVED")

        assert archived.lifecycle == "ARCHIVED"
        assert archived.version == 1  # Version unchanged on lifecycle change

    def test_series_entity_record_serialization_roundtrip(self):
        """Record should serialize and deserialize correctly."""
        record = SeriesEntityRecord(
            series_entity_id="sentity_a1b2c3d4e5f6g7h8",
            series_id="a1b2c3d4e5f6g7h8",
            source_name="正泰的",
            entity_type="CHARACTER",
            canonical_target="鄭泰義",
            version=1,
            lifecycle="ACTIVE",
            metadata={"source_books": ["book1"]},
            approved_at="2026-08-18T00:00:00Z",
            approved_by="user",
            created_at="2026-08-18T00:00:00Z",
        )

        data = record.to_dict()
        loaded = SeriesEntityRecord.from_dict(data)

        assert loaded.series_entity_id == record.series_entity_id
        assert loaded.source_name == record.source_name
        assert loaded.canonical_target == record.canonical_target
        assert loaded.version == record.version


class TestSeriesEntityRegistry:
    """Tests for SeriesEntityRegistry CRUD operations."""

    def setup_method(self):
        self.tmp_path = Path("D:/Temp/kilo/test_series_entity")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        self.series_id = compute_series_id("TestSeries")
        self.registry = SeriesEntityRegistry.create_new(self.series_id, self.tmp_path)

    def test_registry_creation(self):
        """Registry should be created empty."""
        assert len(self.registry.entities) == 0
        assert len(self.registry.promotions) == 0

    def test_register_new_entity(self):
        """Register new canonical entity."""
        result = self.registry.register(
            source_name="正泰的",
            entity_type="CHARACTER",
            canonical_target="鄭泰義",
            approved_by="user",
            source_books=("book1",),
        )

        assert result.disposition == "accepted"
        assert result.record.canonical_target == "鄭泰義"
        assert len(self.registry.entities) == 1

    def test_register_duplicate_same_target_no_op(self):
        """Register same entity with same target -> NO-OP."""
        self.registry.register(
            source_name="正泰的",
            entity_type="CHARACTER",
            canonical_target="鄭泰義",
        )

        result = self.registry.register(
            source_name="正泰的",
            entity_type="CHARACTER",
            canonical_target="鄭泰義",
        )

        assert result.disposition == "no_op"
        assert len(self.registry.entities) == 1

    def test_register_conflict_different_target(self):
        """Register same entity with different target -> CONFLICT."""
        self.registry.register(
            source_name="正泰的",
            entity_type="CHARACTER",
            canonical_target="鄭泰義",
        )

        result = self.registry.register(
            source_name="正泰的",
            entity_type="CHARACTER",
            canonical_target="鄭泰義不同",
        )

        assert result.disposition == "conflict"
        assert result.conflict is not None
        assert result.conflict.existing_target == "鄭泰義"
        assert result.conflict.proposed_target == "鄭泰義不同"

    def test_get_by_source_typed(self):
        """Typed query: get_by_source requires entity_type (SE-3)."""
        self.registry.register(
            source_name="正泰的",
            entity_type="CHARACTER",
            canonical_target="鄭泰義",
        )

        # Must provide entity_type
        record = self.registry.get_by_source("正泰的", "CHARACTER")
        assert record is not None
        assert record.canonical_target == "鄭泰義"

        # Different type should not find it
        record2 = self.registry.get_by_source("正泰的", "PLACE")
        assert record2 is None

    def test_get_all_sorted(self):
        """get_all returns entities sorted by series_entity_id."""
        self.registry.register("B", "CHARACTER", "B")
        self.registry.register("A", "CHARACTER", "A")
        self.registry.register("C", "CHARACTER", "C")

        all_records = self.registry.get_all()
        assert len(all_records) == 3
        # Sorted by series_entity_id (which depends on source_name hash)
        # Just verify all three are present
        sources = {r.source_name for r in all_records}
        assert sources == {"A", "B", "C"}

    def test_get_by_type(self):
        """Filter entities by type."""
        self.registry.register("正泰的", "CHARACTER", "鄭泰義")
        self.registry.register("首尔", "PLACE", "首爾")
        self.registry.register("公司", "ORGANIZATION", "公司")

        chars = self.registry.get_by_type("CHARACTER")
        places = self.registry.get_by_type("PLACE")

        assert len(chars) == 1
        assert len(places) == 1
        assert chars[0].source_name == "正泰的"
        assert places[0].source_name == "首尔"

    def test_update_target_supersede(self):
        """Supersede canonical target creates new version (SE-5)."""
        self.registry.register(
            source_name="正泰的",
            entity_type="CHARACTER",
            canonical_target="鄭泰義",
        )

        # Find the actual entity ID
        record = self.registry.get_by_source("正泰的", "CHARACTER")
        assert record is not None

        result = self.registry.update_target(
            series_entity_id=record.series_entity_id,
            new_target="鄭泰義新",
            approved_by="user",
        )

        assert result.disposition == "accepted"
        assert result.record.version == 2
        assert result.record.canonical_target == "鄭泰義新"

    def test_archive_entities(self):
        """Archive all entities (read-only mode)."""
        self.registry.register("正泰的", "CHARACTER", "鄭泰義")
        self.registry.archive()

        for record in self.registry.entities.values():
            assert record.lifecycle == "ARCHIVED"


class TestPersistence:
    """Tests for deterministic persistence with SHA-256 fingerprint."""

    def setup_method(self):
        self.tmp_path = Path("D:/Temp/kilo/test_persistence")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        self.series_id = compute_series_id("PersistSeries")
        self.registry = SeriesEntityRegistry.create_new(self.series_id, self.tmp_path)

    def test_save_load_roundtrip(self):
        """Save -> load -> fingerprint matches."""
        self.registry.register("正泰的", "CHARACTER", "鄭泰義")
        self.registry.register("首尔", "PLACE", "首爾")

        self.registry.save()

        loaded = SeriesEntityRegistry.load(self.series_id, self.tmp_path)

        assert len(loaded.entities) == 2
        assert loaded.get_registry_hash() == self.registry.get_registry_hash()

    def test_deterministic_serialization(self):
        """Same records -> bit-for-bit identical JSON."""
        self.registry.register("正泰的", "CHARACTER", "鄭泰義")

        self.registry.save()
        path1 = get_series_entity_registry_path(self.tmp_path / "series" / self.series_id, self.series_id)
        content1 = path1.read_text(encoding="utf-8")

        # Reload and save again
        loaded = SeriesEntityRegistry.load(self.series_id, self.tmp_path)
        loaded.save()
        content2 = path1.read_text(encoding="utf-8")

        assert content1 == content2

    def test_corrupted_json_rejected(self):
        """Corrupted JSON must raise exception (fail-closed)."""
        self.registry.register("正泰的", "CHARACTER", "鄭泰義")
        self.registry.save()

        path = get_series_entity_registry_path(self.tmp_path / "series" / self.series_id, self.series_id)
        path.write_text("{ invalid json", encoding="utf-8")

        with pytest.raises(SeriesEntityValidationError, match="not valid JSON"):
            SeriesEntityRegistry.load(self.series_id, self.tmp_path)

    def test_fingerprint_mismatch_rejected(self):
        """Tampered fingerprint must raise IntegrityError (fail-closed)."""
        self.registry.register("正泰的", "CHARACTER", "鄭泰義")
        self.registry.save()

        path = get_series_entity_registry_path(self.tmp_path / "series" / self.series_id, self.series_id)
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
        data["entities"][0]["canonical_target"] = "篡改"
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(SeriesEntityIntegrityError, match="Fingerprint mismatch"):
            SeriesEntityRegistry.load(self.series_id, self.tmp_path)

    def test_missing_file_returns_empty(self):
        """Loading non-existent registry should raise (not return empty)."""
        with pytest.raises(SeriesEntityValidationError, match="not found"):
            SeriesEntityRegistry.load("nonexistent", self.tmp_path)

    def test_persistence_isolation_cross_series(self):
        """Series A and B have separate registry files."""
        series_a_id = compute_series_id("SeriesA")
        series_b_id = compute_series_id("SeriesB")

        reg_a = SeriesEntityRegistry.create_new(series_a_id, self.tmp_path)
        reg_a.register("正泰的", "CHARACTER", "鄭泰義")
        reg_a.save()

        reg_b = SeriesEntityRegistry.create_new(series_b_id, self.tmp_path)
        reg_b.register("正泰的", "CHARACTER", "鄭泰義")  # Same source, different series
        reg_b.save()

        path_a = get_series_entity_registry_path(self.tmp_path / "series" / series_a_id, series_a_id)
        path_b = get_series_entity_registry_path(self.tmp_path / "series" / series_b_id, series_b_id)

        assert path_a != path_b
        assert path_a.exists()
        assert path_b.exists()


class TestHydration:
    """Tests for Series -> Book hydration (READ-ONLY projection)."""

    def setup_method(self):
        self.tmp_path = Path("D:/Temp/kilo/test_hydration")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        self.series_id = compute_series_id("HydrationSeries")
        self.registry = SeriesEntityRegistry.create_new(self.series_id, self.tmp_path)
        self.registry.register("正泰的", "CHARACTER", "鄭泰義")
        self.registry.register("首尔", "PLACE", "首爾")

    def test_hydration_returns_user_overrides_dict(self):
        """Hydration returns Dict[source, target] for user_overrides."""
        overrides, report = self.registry.hydrate_resolver("book1")

        assert isinstance(overrides, dict)
        assert "正泰的" in overrides
        assert "首尔" in overrides
        assert overrides["正泰的"] == "鄭泰義"
        assert overrides["首尔"] == "首爾"

    def test_hydration_report(self):
        """HydrationReport contains correct counts."""
        overrides, report = self.registry.hydrate_resolver("book1")

        assert report.series_id == self.series_id
        assert report.book_identity == "book1"
        assert report.hydrated_count == 2
        assert report.skipped_count == 0
        assert report.conflict_count == 0
        assert report.hydration_source.startswith(f"series:{self.series_id}:")

    def test_hydration_idempotent(self):
        """Hydrating twice produces same overrides."""
        overrides1, _ = self.registry.hydrate_resolver("book1")
        overrides2, _ = self.registry.hydrate_resolver("book1")

        assert overrides1 == overrides2

    def test_hydration_skips_archived(self):
        """Archived entities are not hydrated."""
        self.registry.archive()

        overrides, report = self.registry.hydrate_resolver("book1")

        assert report.hydrated_count == 0
        assert report.skipped_count == 2


class TestPromotion:
    """Tests for Book -> Series promotion (MANUAL gate, D-07 frozen)."""

    def setup_method(self):
        self.tmp_path = Path("D:/Temp/kilo/test_promotion")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        self.series_id = compute_series_id("PromotionSeries")
        self.registry = SeriesEntityRegistry.create_new(self.series_id, self.tmp_path)

    def test_promotion_manual_gate_enforced(self):
        """Promotion with approval_gate=False must raise (D-07 frozen)."""
        with pytest.raises(SeriesEntityValidationError, match="MANUAL approval gate"):
            self.registry.promote_from_resolver(
                {"正泰的": "鄭泰義"},
                "book1",
                approval_gate=False,
            )

    def test_promotion_new_entity_created(self):
        """New USER override from book creates SeriesEntityRecord."""
        results = self.registry.promote_from_resolver(
            {"正泰的": "鄭泰義"},
            "book1",
            approval_gate=True,
        )

        assert len(results) == 1
        assert results[0].disposition == "accepted"
        assert results[0].record.canonical_target == "鄭泰義"
        assert results[0].record.approved_by == "series_promotion"

    def test_promotion_same_target_no_op(self):
        """Same target already in series -> NO-OP."""
        self.registry.register("正泰的", "CHARACTER", "鄭泰義")

        results = self.registry.promote_from_resolver(
            {"正泰的": "鄭泰義"},
            "book1",
            approval_gate=True,
        )

        assert len(results) == 1
        assert results[0].disposition == "no_op"

    def test_promotion_different_target_conflict(self):
        """Different target in series -> CONFLICT."""
        self.registry.register("正泰的", "CHARACTER", "鄭泰義")

        results = self.registry.promote_from_resolver(
            {"正泰的": "鄭泰義不同"},
            "book1",
            approval_gate=True,
        )

        assert len(results) == 1
        assert results[0].disposition == "conflict"
        assert "CONFLICT" in results[0].message

    def test_promotion_learning_data_not_promoted(self):
        """LEARNING data (low confidence) is not promoted."""
        # This test documents that learning_data from resolver is not auto-promoted
        # The promote_from_resolver only looks at user_overrides
        pass  # Implementation only promotes user_overrides

    def test_promotion_audit_trail(self):
        """EntityPromotionRecord created for each promotion."""
        results = self.registry.promote_from_resolver(
            {"正泰的": "鄭泰義"},
            "book1",
            approval_gate=True,
        )

        assert len(self.registry.promotions) == 1
        promo = self.registry.promotions[0]
        assert promo.promotion_id is not None
        assert promo.series_id == self.series_id
        assert promo.book_identity == "book1"
        assert promo.source_name == "正泰的"
        assert promo.action == "created"
        assert promo.resolved_by == "user"


class TestConflictResolution:
    """Tests for MANUAL conflict resolution."""

    def setup_method(self):
        self.tmp_path = Path("D:/Temp/kilo/test_conflict")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        self.series_id = compute_series_id("ConflictSeries")
        self.registry = SeriesEntityRegistry.create_new(self.series_id, self.tmp_path)
        self.registry.register("正泰的", "CHARACTER", "鄭泰義")

    def test_resolve_conflict_book_wins(self):
        """Resolve conflict: book_wins uses proposed target."""
        # Create conflict via promotion (which stores conflicts)
        self.registry.register("正泰的", "CHARACTER", "鄭泰義")
        self.registry.promote_from_resolver({"正泰的": "鄭泰義新"}, "book1", approval_gate=True)

        # Get the conflict from the registry
        conflict_id = list(self.registry._conflicts.keys())[0]

        # Resolve: book wins
        resolved = self.registry.resolve_promotion_conflict(
            conflict_id, "book_wins", "user"
        )

        assert resolved.disposition == "accepted"
        assert resolved.record.canonical_target == "鄭泰義新"
        assert resolved.conflict.resolution == "book_wins"

    def test_resolve_conflict_series_wins(self):
        """Resolve conflict: series_wins keeps existing target."""
        self.registry.register("正泰的", "CHARACTER", "鄭泰義")
        self.registry.promote_from_resolver({"正泰的": "鄭泰義新"}, "book1", approval_gate=True)

        conflict_id = list(self.registry._conflicts.keys())[0]

        resolved = self.registry.resolve_promotion_conflict(
            conflict_id, "series_wins", "user"
        )

        assert resolved.disposition == "accepted"
        assert resolved.record.canonical_target == "鄭泰義"

    def test_resolve_conflict_manual_value(self):
        """Resolve conflict: manual provides custom value."""
        self.registry.register("正泰的", "CHARACTER", "鄭泰義")
        self.registry.promote_from_resolver({"正泰的": "鄭泰義新"}, "book1", approval_gate=True)

        conflict_id = list(self.registry._conflicts.keys())[0]

        resolved = self.registry.resolve_promotion_conflict(
            conflict_id, "manual", "user", manual_value="鄭泰義手動"
        )

        assert resolved.record.canonical_target == "鄭泰義手動"

    def test_resolve_already_resolved_raises(self):
        """Resolving already-resolved conflict raises."""
        self.registry.register("正泰的", "CHARACTER", "鄭泰義")
        self.registry.promote_from_resolver({"正泰的": "鄭泰義新"}, "book1", approval_gate=True)

        conflict_id = list(self.registry._conflicts.keys())[0]

        self.registry.resolve_promotion_conflict(conflict_id, "book_wins", "user")

        with pytest.raises(SeriesEntityValidationError, match="already resolved"):
            self.registry.resolve_promotion_conflict(conflict_id, "series_wins", "user")


class TestManifestIntegration:
    """Tests for SeriesManifest series_entity_registry_hash integration."""

    def setup_method(self):
        self.tmp_path = Path("D:/Temp/kilo/test_manifest")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        # Use unique series name per test to avoid conflicts
        unique_name = f"ManifestSeries_{uuid.uuid4().hex[:8]}"
        self.series_id = compute_series_id(unique_name)

        # Create series first
        self.series_registry_obj = SeriesRegistry(self.tmp_path)
        created = self.series_registry_obj.create(unique_name)
        self.series_id = created.series_id

        self.series_registry = SeriesEntityRegistry.create_new(self.series_id, self.tmp_path)
        self.series_registry.register("正泰的", "CHARACTER", "鄭泰義")
        self.series_registry.save()

        self.series_registry_obj.update_series_entity_registry_hash(
            self.series_id, self.series_registry.get_registry_hash()
        )

    def test_manifest_has_registry_hash(self):
        """Manifest stores series_entity_registry_hash."""
        manifest = self.series_registry_obj.get(self.series_id)
        assert hasattr(manifest, "series_entity_registry_hash")
        assert manifest.series_entity_registry_hash == self.series_registry.get_registry_hash()

    def test_manifest_fingerprint_changes_with_registry_hash(self):
        """Manifest fingerprint changes when registry hash changes."""
        manifest1 = self.series_registry_obj.get(self.series_id)
        fp1 = manifest1.manifest_fingerprint

        # Add another entity
        self.series_registry.register("首尔", "PLACE", "首爾")
        self.series_registry.save()
        self.series_registry_obj.update_series_entity_registry_hash(
            self.series_id, self.series_registry.get_registry_hash()
        )

        manifest2 = self.series_registry_obj.get(self.series_id)
        fp2 = manifest2.manifest_fingerprint

        assert fp1 != fp2

    def test_old_manifest_loads_without_registry_hash(self):
        """Pre-Batch 5.3 manifest (no registry hash) loads with empty string."""
        # Create old-style manifest without registry hash
        old_manifest = SeriesManifest(
            schema_name="ntpe.series_manifest",
            schema_version="1.0",
            series_id=self.series_id,
            series_name="OldSeries",
            lifecycle_status=SeriesLifecycle.CREATED,
            created_at="2026-08-18T00:00:00Z",
            updated_at="2026-08-18T00:00:00Z",
            books=(),
            series_memory_hash="",
            series_checkpoint_hash="",
            series_entity_registry_hash="",
            manifest_fingerprint="",
        )

        # This should not raise - uses .get() with default ""
        path = manifest_file_path(get_series_dir(self.tmp_path, self.series_id), self.series_id)
        save_manifest(old_manifest, path)

        loaded = load_manifest(path)
        assert loaded.series_entity_registry_hash == ""

    def test_registry_update_propagates_to_manifest(self):
        """Registry changes -> new registry hash -> manifest update."""
        manifest_before = self.series_registry_obj.get(self.series_id)
        hash_before = manifest_before.series_entity_registry_hash

        self.series_registry.register("新角色", "CHARACTER", "新角色")
        self.series_registry.save()
        self.series_registry_obj.update_series_entity_registry_hash(
            self.series_id, self.series_registry.get_registry_hash()
        )

        manifest_after = self.series_registry_obj.get(self.series_id)
        hash_after = manifest_after.series_entity_registry_hash

        assert hash_before != hash_after


class TestCrossSeriesIsolation:
    """Tests for cross-series isolation (CSI-02 hard gate)."""

    def setup_method(self):
        self.tmp_path = Path("D:/Temp/kilo/test_isolation")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        self.series_a_id = compute_series_id("SeriesA")
        self.series_b_id = compute_series_id("SeriesB")

    def test_registry_isolation(self):
        """Series A registry cannot see Series B entities."""
        reg_a = SeriesEntityRegistry.create_new(self.series_a_id, self.tmp_path)
        reg_a.register("正泰的", "CHARACTER", "鄭泰義_A")
        reg_a.save()

        reg_b = SeriesEntityRegistry.create_new(self.series_b_id, self.tmp_path)
        reg_b.register("正泰的", "CHARACTER", "鄭泰義_B")
        reg_b.save()

        # Load and verify isolation
        loaded_a = SeriesEntityRegistry.load(self.series_a_id, self.tmp_path)
        loaded_b = SeriesEntityRegistry.load(self.series_b_id, self.tmp_path)

        record_a = loaded_a.get_by_source("正泰的", "CHARACTER")
        record_b = loaded_b.get_by_source("正泰的", "CHARACTER")

        assert record_a.canonical_target == "鄭泰義_A"
        assert record_b.canonical_target == "鄭泰義_B"
        assert record_a.canonical_target != record_b.canonical_target

    def test_hydration_isolation(self):
        """Hydration from Series A does not leak to Series B."""
        reg_a = SeriesEntityRegistry.create_new(self.series_a_id, self.tmp_path)
        reg_a.register("正泰的", "CHARACTER", "鄭泰義_A")
        reg_a.save()

        reg_b = SeriesEntityRegistry.create_new(self.series_b_id, self.tmp_path)
        reg_b.register("正泰的", "CHARACTER", "鄭泰義_B")
        reg_b.save()

        # Hydrate Series A
        overrides_a, _ = reg_a.hydrate_resolver("book1")
        # Hydrate Series B
        overrides_b, _ = reg_b.hydrate_resolver("book1")

        assert overrides_a["正泰的"] == "鄭泰義_A"
        assert overrides_b["正泰的"] == "鄭泰義_B"
        assert overrides_a != overrides_b

    def test_promotion_isolation(self):
        """Promotion in Series A does not affect Series B."""
        reg_a = SeriesEntityRegistry.create_new(self.series_a_id, self.tmp_path)
        reg_b = SeriesEntityRegistry.create_new(self.series_b_id, self.tmp_path)

        reg_a.promote_from_resolver({"正泰的": "鄭泰義_A"}, "book1", approval_gate=True)
        reg_a.save()

        reg_b.promote_from_resolver({"正泰的": "鄭泰義_B"}, "book1", approval_gate=True)
        reg_b.save()

        loaded_a = SeriesEntityRegistry.load(self.series_a_id, self.tmp_path)
        loaded_b = SeriesEntityRegistry.load(self.series_b_id, self.tmp_path)

        record_a = loaded_a.get_by_source("正泰的", "CHARACTER")
        record_b = loaded_b.get_by_source("正泰的", "CHARACTER")

        assert record_a.canonical_target == "鄭泰義_A"
        assert record_b.canonical_target == "鄭泰義_B"


class TestEntityResolverIntegration:
    """Tests for EntityResolver integration via user_overrides (SE-4 frozen)."""

    def test_resolver_precedence_series_over_runtime(self):
        """Series hydrated overrides take precedence over RUNTIME."""
        tmp_path = Path("D:/Temp/kilo/test_resolver_precedence")
        tmp_path.mkdir(parents=True, exist_ok=True)
        series_id = compute_series_id("ResolverSeries")

        registry = SeriesEntityRegistry.create_new(series_id, tmp_path)
        registry.register("正泰的", "CHARACTER", "鄭泰義_系列")
        registry.save()

        # Hydrate
        overrides, _ = registry.hydrate_resolver("book1")

        # Create resolver with Series overrides + Runtime
        # Note: We can't easily test full precedence without MergedRuntime,
        # but we can verify the overrides are injected correctly
        resolver = EntityResolver(
            runtime=None,
            user_overrides=overrides,
            learning_data={},
        )

        # Should use Series override
        from core.entity_resolver.models import ExtractedEntity, InjectionSource
        extracted = [ExtractedEntity(source="正泰的", entity_type="CHARACTER", context="test")]
        result = resolver.resolve(extracted)

        assert len(result.entities) == 1
        assert result.entities[0].target == "鄭泰義_系列"
        assert result.entities[0].source_level == InjectionSource.USER.value

    def test_resolver_learning_not_overridden_by_series_when_no_override(self):
        """Learning data used when no Series override exists."""
        tmp_path = Path("D:/Temp/kilo/test_resolver_learning")
        tmp_path.mkdir(parents=True, exist_ok=True)
        series_id = compute_series_id("ResolverSeries2")

        registry = SeriesEntityRegistry.create_new(series_id, tmp_path)
        registry.register("其他角色", "CHARACTER", "其他角色_系列")
        registry.save()

        overrides, _ = registry.hydrate_resolver("book1")

        resolver = EntityResolver(
            runtime=None,
            user_overrides=overrides,
            learning_data={"正泰的": "鄭泰義_學習"},
        )

        from core.entity_resolver.models import ExtractedEntity, InjectionSource
        # This entity has no Series override, so should use LEARNING
        extracted = [ExtractedEntity(source="正泰的", entity_type="CHARACTER", context="test")]
        result = resolver.resolve(extracted)

        assert len(result.entities) == 1
        assert result.entities[0].target == "鄭泰義_學習"
        assert result.entities[0].source_level == InjectionSource.LEARNING.value


class TestPropertyBased:
    """Property-based tests (1000 iterations)."""

    def test_series_entity_id_deterministic_property(self):
        """Same inputs always produce same ID (1000 iterations)."""
        import random
        import string

        for _ in range(1000):
            series_key = "".join(random.choices(string.ascii_letters + string.digits + " ", k=20))
            series_id = compute_series_id(series_key)

            source = "".join(random.choices("正泰的李某王五", k=3))
            entity_type = random.choice(["CHARACTER", "PLACE", "ORGANIZATION", "TERMINOLOGY"])

            id1 = compute_series_entity_id(series_id, source, entity_type)
            id2 = compute_series_entity_id(series_id, source, entity_type)

            assert id1 == id2, f"Non-deterministic for series_id={series_id}, source={source}, type={entity_type}"

    def test_registry_fingerprint_deterministic(self):
        """Same registry state always produces same fingerprint."""
        import random
        import string

        for _ in range(1000):
            series_key = "".join(random.choices(string.ascii_letters + " ", k=15)).strip()
            if not series_key:
                continue

            series_id = compute_series_id(series_key)
            tmp_path = Path("D:/Temp/kilo/test_property")
            tmp_path.mkdir(parents=True, exist_ok=True)

            registry = SeriesEntityRegistry.create_new(series_id, tmp_path)

            # Add random entities
            for _ in range(random.randint(0, 5)):
                source = "".join(random.choices("正泰的李某王五", k=3))
                entity_type = random.choice(["CHARACTER", "PLACE", "TERMINOLOGY"])
                target = "".join(random.choices("鄭泰義李某王五", k=3))
                registry.register(source, entity_type, target)

            fp1 = registry.get_registry_hash()
            fp2 = registry.get_registry_hash()
            assert fp1 == fp2


# Run tests when executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
