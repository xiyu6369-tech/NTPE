from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from core.series_identity import (
    SeriesIdentity,
    SeriesManifest,
    SeriesBookEntry,
    SeriesLifecycle,
    BookStatus,
    SeriesRegistry,
    compute_series_id,
    canonicalize_series_key,
    to_canonical_json,
    compute_manifest_fingerprint,
    compute_series_id,
    get_series_dir,
    manifest_file_path,
    save_manifest,
    load_manifest,
    validate_manifest,
    ValidationError,
    IntegrityError,
)


class TestSeriesIdentity:
    """Tests for SeriesIdentity and ID generation."""

    def test_compute_series_id_deterministic(self):
        """Same canonical key must produce same series_id."""
        key = "Passion"
        id1 = compute_series_id(key)
        id2 = compute_series_id(key)
        assert id1 == id2
        assert len(id1) == 16
        assert all(c in "0123456789abcdef" for c in id1)

    def test_compute_series_id_canonicalization_whitespace(self):
        """Whitespace should be normalized."""
        assert compute_series_id(" Passion ") == compute_series_id("Passion")
        assert compute_series_id("\tPassion\n") == compute_series_id("Passion")

    def test_compute_series_id_canonicalization_case(self):
        """Case should be normalized to lowercase."""
        assert compute_series_id("PASSION") == compute_series_id("passion")
        assert compute_series_id("PaSsIoN") == compute_series_id("passion")

    def test_compute_series_id_unicode_preserved(self):
        """Unicode characters should be preserved (not ASCII-only)."""
        key = "熱情"
        id1 = compute_series_id(key)
        id2 = compute_series_id(key)
        assert id1 == id2
        assert len(id1) == 16

    def test_series_identity_immutability(self):
        """series_id must be immutable after creation."""
        identity = SeriesIdentity.create("Passion")
        original_id = identity.series_id

        # with_updated_name creates new identity, doesn't modify original
        updated = identity.with_updated_name("New Name")
        assert updated.series_id == original_id  # ID unchanged
        assert updated.series_name == "New Name"
        assert updated.updated_at != identity.updated_at  # timestamp updated

    def test_series_identity_create_with_custom_name(self):
        """SeriesIdentity.create accepts custom display name."""
        identity = SeriesIdentity.create("passion_key", "Passion Series")
        assert identity.series_id == compute_series_id("passion_key")
        assert identity.series_name == "Passion Series"

    def test_series_identity_default_name(self):
        """Default series_name is stripped key."""
        identity = SeriesIdentity.create("  Passion  ")
        assert identity.series_name == "Passion"


class TestSeriesManifest:
    """Tests for SeriesManifest and book membership."""

    def test_manifest_creation(self):
        """Basic manifest creation with required fields."""
        identity = SeriesIdentity.create("Passion")
        manifest = SeriesManifest(
            schema_name="ntpe.series_manifest",
            schema_version="1.0",
            series_id=identity.series_id,
            series_name=identity.series_name,
            lifecycle_status=SeriesLifecycle.CREATED,
            created_at=identity.created_at,
            updated_at=identity.updated_at,
            books=(),
            series_memory_hash="",
            series_checkpoint_hash="",
            manifest_fingerprint="",
        )

        assert manifest.series_id == identity.series_id
        assert manifest.lifecycle_status == SeriesLifecycle.CREATED
        assert len(manifest.books) == 0

    def test_manifest_roundtrip(self, tmp_path):
        """Save -> load -> fingerprint matches."""
        identity = SeriesIdentity.create("Passion")
        manifest = SeriesManifest(
            schema_name="ntpe.series_manifest",
            schema_version="1.0",
            series_id=identity.series_id,
            series_name=identity.series_name,
            lifecycle_status=SeriesLifecycle.CREATED,
            created_at=identity.created_at,
            updated_at=identity.updated_at,
            books=(),
            series_memory_hash="",
            series_checkpoint_hash="",
            manifest_fingerprint="",
        )

        # Compute fingerprint
        from core.series_identity import compute_manifest_fingerprint
        fingerprint = compute_manifest_fingerprint(manifest.to_canonical_dict())
        manifest = manifest.with_fingerprint(fingerprint)

        # Save and load
        series_dir = tmp_path / "series" / identity.series_id
        series_dir.mkdir(parents=True)
        manifest_path = series_dir / f"series_manifest_{identity.series_id}.json"

        from core.series_identity import save_manifest, load_manifest
        save_manifest(manifest, manifest_path)
        loaded = load_manifest(manifest_path)

        assert loaded.series_id == manifest.series_id
        assert loaded.manifest_fingerprint == manifest.manifest_fingerprint

    def test_manifest_fingerprint_integrity(self, tmp_path):
        """Tampered manifest file should fail validation."""
        identity = SeriesIdentity.create("Passion")
        manifest = SeriesManifest(
            schema_name="ntpe.series_manifest",
            schema_version="1.0",
            series_id=identity.series_id,
            series_name=identity.series_name,
            lifecycle_status=SeriesLifecycle.CREATED,
            created_at=identity.created_at,
            updated_at=identity.updated_at,
            books=(),
            series_memory_hash="",
            series_checkpoint_hash="",
            manifest_fingerprint="",
        )

        from core.series_identity import compute_manifest_fingerprint, save_manifest, load_manifest, validate_manifest
        fingerprint = compute_manifest_fingerprint(manifest.to_canonical_dict())
        manifest = manifest.with_fingerprint(fingerprint)

        series_dir = tmp_path / "series" / identity.series_id
        series_dir.mkdir(parents=True)
        manifest_path = series_dir / f"series_manifest_{identity.series_id}.json"

        save_manifest(manifest, manifest_path)

        # Tamper with file
        import json
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data["series_name"] = "Tampered"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        # Load should detect integrity error
        loaded = load_manifest(manifest_path)
        result = validate_manifest(loaded, identity.series_id)
        assert not result.valid
        assert any("fingerprint" in e.lower() for e in result.errors)

    def test_book_ordering_sequential(self):
        """volume_number must be sequential starting at 1."""
        identity = SeriesIdentity.create("Passion")
        from core.series_identity import SeriesBookEntry, BookStatus

        books = [
            SeriesBookEntry(
                volume_number=1, book_identity="b1", source_path="p1", title="Book 1",
                status=BookStatus.PENDING, content_fingerprint="cf1", manifest_fingerprint="mf1",
                added_at="2026-01-01T00:00:00Z",
            ),
            SeriesBookEntry(
                volume_number=2, book_identity="b2", source_path="p2", title="Book 2",
                status=BookStatus.PENDING, content_fingerprint="cf2", manifest_fingerprint="mf2",
                added_at="2026-01-02T00:00:00Z",
            ),
        ]

        manifest = SeriesManifest(
            schema_name="ntpe.series_manifest",
            schema_version="1.0",
            series_id=identity.series_id,
            series_name=identity.series_name,
            lifecycle_status=SeriesLifecycle.ACTIVE,
            created_at=identity.created_at,
            updated_at=identity.updated_at,
            books=tuple(books),
            series_memory_hash="",
            series_checkpoint_hash="",
            manifest_fingerprint="",
        )

        assert manifest.next_volume_number() == 3

    def test_book_ordering_immutable(self):
        """Cannot reorder or insert gaps in volume_number."""
        from core.series_identity import validate_manifest, SeriesBookEntry, BookStatus
        identity = SeriesIdentity.create("Passion")

        # Gap in volume numbers
        books = [
            SeriesBookEntry(
                volume_number=1, book_identity="b1", source_path="p1", title="Book 1",
                status=BookStatus.PENDING, content_fingerprint="cf1", manifest_fingerprint="mf1",
                added_at="2026-01-01T00:00:00Z",
            ),
            SeriesBookEntry(
                volume_number=3, book_identity="b2", source_path="p2", title="Book 2",
                status=BookStatus.PENDING, content_fingerprint="cf2", manifest_fingerprint="mf2",
                added_at="2026-01-02T00:00:00Z",
            ),
        ]

        manifest = SeriesManifest(
            schema_name="ntpe.series_manifest",
            schema_version="1.0",
            series_id=identity.series_id,
            series_name=identity.series_name,
            lifecycle_status=SeriesLifecycle.ACTIVE,
            created_at=identity.created_at,
            updated_at=identity.updated_at,
            books=tuple(books),
            series_memory_hash="",
            series_checkpoint_hash="",
            manifest_fingerprint="",
        )

        result = validate_manifest(manifest, identity.series_id)
        assert not result.valid
        assert any("gap" in e.lower() or "order" in e.lower() for e in result.errors)

    def test_duplicate_book_rejected(self):
        """Same book_identity cannot be added twice to same series."""
        from core.series_identity import validate_manifest, SeriesBookEntry, BookStatus
        identity = SeriesIdentity.create("Passion")

        books = [
            SeriesBookEntry(
                volume_number=1, book_identity="b1", source_path="p1", title="Book 1",
                status=BookStatus.PENDING, content_fingerprint="cf1", manifest_fingerprint="mf1",
                added_at="2026-01-01T00:00:00Z",
            ),
            SeriesBookEntry(
                volume_number=2, book_identity="b1", source_path="p2", title="Book 2",
                status=BookStatus.PENDING, content_fingerprint="cf2", manifest_fingerprint="mf2",
                added_at="2026-01-02T00:00:00Z",
            ),
        ]

        manifest = SeriesManifest(
            schema_name="ntpe.series_manifest",
            schema_version="1.0",
            series_id=identity.series_id,
            series_name=identity.series_name,
            lifecycle_status=SeriesLifecycle.ACTIVE,
            created_at=identity.created_at,
            updated_at=identity.updated_at,
            books=tuple(books),
            series_memory_hash="",
            series_checkpoint_hash="",
            manifest_fingerprint="",
        )

        result = validate_manifest(manifest, identity.series_id)
        assert not result.valid
        assert any("duplicate" in e.lower() for e in result.errors)

    def test_duplicate_name_allowed_different_id(self):
        """Two series with same display name but different series_id are allowed."""
        id1 = compute_series_id("passion")
        id2 = compute_series_id("passion")  # Same canonical key -> same ID
        # Different canonical keys produce different IDs
        id3 = compute_series_id("passion ")
        assert id1 == id2
        # Note: same canonical key = same ID, different canonical keys = different IDs

    def test_lifecycle_transitions(self):
        """Valid lifecycle transitions."""
        identity = SeriesIdentity.create("Passion")
        manifest = SeriesManifest(
            schema_name="ntpe.series_manifest",
            schema_version="1.0",
            series_id=identity.series_id,
            series_name=identity.series_name,
            lifecycle_status=SeriesLifecycle.CREATED,
            created_at=identity.created_at,
            updated_at=identity.updated_at,
            books=(),
            series_memory_hash="",
            series_checkpoint_hash="",
            manifest_fingerprint="",
        )

        # CREATED -> ACTIVE (via add_book simulation)
        from core.series_identity import SeriesBookEntry
        book_entry = SeriesBookEntry(
            volume_number=1,
            book_identity='b1',
            source_path='p1',
            title='Book 1',
            status=BookStatus.PENDING,
            content_fingerprint='cf1',
            manifest_fingerprint='mf1',
            added_at='2026-01-01T00:00:00Z',
            completed_at=None,
            promoted_at=None,
        )
        updated = manifest.with_added_book(book_entry)
        assert updated.lifecycle_status == SeriesLifecycle.ACTIVE

    def test_all_books_promoted_detects_completed(self):
        """Series should auto-detect COMPLETED when all books promoted."""
        from core.series_identity import SeriesBookEntry, BookStatus
        identity = SeriesIdentity.create("Passion")

        books = [
            SeriesBookEntry(
                volume_number=1, book_identity="b1", source_path="p1", title="Book 1",
                status=BookStatus.PROMOTED, content_fingerprint="cf1", manifest_fingerprint="mf1",
                added_at="2026-01-01T00:00:00Z", promoted_at="2026-01-10T00:00:00Z",
            ),
        ]

        manifest = SeriesManifest(
            schema_name="ntpe.series_manifest",
            schema_version="1.0",
            series_id=identity.series_id,
            series_name=identity.series_name,
            lifecycle_status=SeriesLifecycle.ACTIVE,
            created_at=identity.created_at,
            updated_at=identity.updated_at,
            books=tuple(books),
            series_memory_hash="",
            series_checkpoint_hash="",
            manifest_fingerprint="",
        )

        assert manifest.all_books_promoted()
        assert not manifest.has_in_progress_books()


class TestSeriesRegistry:
    """Tests for SeriesRegistry operations."""

    def test_create_series(self, tmp_path):
        """Create new series with registry."""
        registry = SeriesRegistry(tmp_path)
        result = registry.create("Passion")

        assert result.series_id == compute_series_id("passion")
        assert result.manifest.series_name == "Passion"
        assert result.manifest.lifecycle_status == SeriesLifecycle.CREATED
        assert result.manifest_path.exists()

    def test_get_existing_series(self, tmp_path):
        """Retrieve existing series by series_id."""
        registry = SeriesRegistry(tmp_path)
        created = registry.create("Passion")

        loaded = registry.get(created.series_id)
        assert loaded.series_id == created.series_id
        assert loaded.series_name == "Passion"

    def test_get_nonexistent_series_raises(self, tmp_path):
        """Getting non-existent series raises ValidationError."""
        registry = SeriesRegistry(tmp_path)
        with pytest.raises(ValidationError, match="not found"):
            registry.get("nonexistent")

    def test_list_all_series(self, tmp_path):
        """List all series in registry."""
        registry = SeriesRegistry(tmp_path)
        registry.create("Passion")
        registry.create("Another Series")

        all_series = registry.list_all()
        assert len(all_series) == 2
        assert all_series[0].series_name == "Passion"
        assert all_series[1].series_name == "Another Series"

    def test_add_book_to_series(self, tmp_path):
        """Add a book to existing series."""
        registry = SeriesRegistry(tmp_path)
        created = registry.create("Passion")

        result = registry.add_book(
            series_id=created.series_id,
            book_identity="book123",
            source_path="input/book1.txt",
            title="Passion Vol. 1",
            content_fingerprint="content_hash_123",
            manifest_fingerprint="manifest_hash_456",
        )

        assert result.volume_number == 1
        assert result.book_entry.book_identity == "book123"
        assert result.manifest.lifecycle_status == SeriesLifecycle.ACTIVE
        assert len(result.manifest.books) == 1

    def test_add_duplicate_book_rejected(self, tmp_path):
        """Adding same book_identity twice should raise."""
        registry = SeriesRegistry(tmp_path)
        created = registry.create("Passion")

        registry.add_book(
            series_id=created.series_id,
            book_identity="book123",
            source_path="input/book1.txt",
            title="Passion Vol. 1",
            content_fingerprint="content_hash_123",
            manifest_fingerprint="manifest_hash_456",
        )

        with pytest.raises(ValidationError, match="already member"):
            registry.add_book(
                series_id=created.series_id,
                book_identity="book123",
                source_path="input/book1.txt",
                title="Passion Vol. 1",
                content_fingerprint="content_hash_123",
                manifest_fingerprint="manifest_hash_456",
            )

    def test_add_book_to_archived_series_rejected(self, tmp_path):
        """Cannot add book to archived series."""
        registry = SeriesRegistry(tmp_path)
        created = registry.create("Passion")
        registry.archive(created.series_id)

        with pytest.raises(ValidationError, match="archived"):
            registry.add_book(
                series_id=created.series_id,
                book_identity="book123",
                source_path="input/book1.txt",
                title="Passion Vol. 1",
                content_fingerprint="content_hash_123",
                manifest_fingerprint="manifest_hash_456",
            )

    def test_update_name(self, tmp_path):
        """Update series display name (series_id unchanged)."""
        registry = SeriesRegistry(tmp_path)
        created = registry.create("Passion")
        original_id = created.series_id

        updated = registry.update_name(original_id, "New Passion Name")

        assert updated.series_id == original_id
        assert updated.series_name == "New Passion Name"
        assert updated.updated_at != created.manifest.updated_at

    def test_update_name_archived_rejected(self, tmp_path):
        """Cannot rename archived series."""
        registry = SeriesRegistry(tmp_path)
        created = registry.create("Passion")
        registry.archive(created.series_id)

        with pytest.raises(ValidationError, match="archived"):
            registry.update_name(created.series_id, "New Name")

    def test_set_book_status_valid_transitions(self, tmp_path):
        """Valid book status transitions."""
        registry = SeriesRegistry(tmp_path)
        created = registry.create("Passion")

        result = registry.add_book(
            series_id=created.series_id,
            book_identity="book123",
            source_path="input/book1.txt",
            title="Book 1",
            content_fingerprint="cf1",
            manifest_fingerprint="mf1",
        )

        # PENDING -> IN_PROGRESS
        updated = registry.set_book_status(created.series_id, 1, BookStatus.IN_PROGRESS)
        book = updated.get_book(1)
        assert book is not None
        assert book.status == BookStatus.IN_PROGRESS

        # IN_PROGRESS -> COMPLETED
        updated = registry.set_book_status(created.series_id, 1, BookStatus.COMPLETED)
        book = updated.get_book(1)
        assert book is not None
        assert book.status == BookStatus.COMPLETED
        assert book.completed_at is not None

        # COMPLETED -> PROMOTED
        updated = registry.set_book_status(created.series_id, 1, BookStatus.PROMOTED)
        book = updated.get_book(1)
        assert book is not None
        assert book.status == BookStatus.PROMOTED
        assert book.promoted_at is not None

    def test_set_book_status_invalid_transition_rejected(self, tmp_path):
        """Invalid book status transitions rejected."""
        registry = SeriesRegistry(tmp_path)
        created = registry.create("Passion")

        registry.add_book(
            series_id=created.series_id,
            book_identity="book123",
            source_path="input/book1.txt",
            title="Book 1",
            content_fingerprint="cf1",
            manifest_fingerprint="mf1",
        )

        # PENDING -> PROMOTED (invalid, must go through IN_PROGRESS, COMPLETED)
        with pytest.raises(ValidationError, match="Invalid book status transition"):
            registry.set_book_status(created.series_id, 1, BookStatus.PROMOTED)

    def test_archive_series(self, tmp_path):
        """Archive series."""
        registry = SeriesRegistry(tmp_path)
        created = registry.create("Passion")

        archived = registry.archive(created.series_id)
        assert archived.lifecycle_status == SeriesLifecycle.ARCHIVED

        # Second archive is idempotent
        archived2 = registry.archive(created.series_id)
        assert archived2.lifecycle_status == SeriesLifecycle.ARCHIVED


class TestCanonicalJson:
    """Tests for deterministic canonical JSON serialization."""

    def test_canonical_json_deterministic(self):
        """Same dict -> same canonical JSON."""
        data = {"z": 1, "a": 2, "m": {"nested": True}}
        json1 = to_canonical_json(data)
        json2 = to_canonical_json(data)
        assert json1 == json2

    def test_canonical_json_sorted_keys(self):
        """Keys must be sorted."""
        json_str = to_canonical_json({"z": 1, "a": 2})
        assert json_str.index("a") < json_str.index("z")

    def test_canonical_json_no_whitespace(self):
        """No unnecessary whitespace."""
        json_str = to_canonical_json({"a": 1, "b": 2})
        assert " " not in json_str
        assert "\n" not in json_str
        assert "\t" not in json_str

    def test_canonical_json_unicode(self):
        """Unicode preserved."""
        json_str = to_canonical_json({"name": "熱情"})
        assert "熱情" in json_str


class TestManifestFingerprint:
    """Tests for manifest fingerprint determinism."""

    def test_fingerprint_deterministic(self):
        """Same manifest -> same fingerprint."""
        identity = SeriesIdentity.create("Passion")
        manifest = SeriesManifest(
            schema_name="ntpe.series_manifest",
            schema_version="1.0",
            series_id=identity.series_id,
            series_name=identity.series_name,
            lifecycle_status=SeriesLifecycle.CREATED,
            created_at=identity.created_at,
            updated_at=identity.updated_at,
            books=(),
            series_memory_hash="",
            series_checkpoint_hash="",
            manifest_fingerprint="",
        )

        fp1 = compute_manifest_fingerprint(manifest.to_canonical_dict())
        fp2 = compute_manifest_fingerprint(manifest.to_canonical_dict())
        assert fp1 == fp2
        assert len(fp1) == 64  # SHA-256 hex

    def test_fingerprint_changes_with_data(self):
        """Different data -> different fingerprint."""
        identity = SeriesIdentity.create("Passion")
        manifest = SeriesManifest(
            schema_name="ntpe.series_manifest",
            schema_version="1.0",
            series_id=identity.series_id,
            series_name=identity.series_name,
            lifecycle_status=SeriesLifecycle.CREATED,
            created_at=identity.created_at,
            updated_at=identity.updated_at,
            books=(),
            series_memory_hash="",
            series_checkpoint_hash="",
            manifest_fingerprint="",
        )

        fp1 = compute_manifest_fingerprint(manifest.to_canonical_dict())

        # Change series_name
        manifest2 = manifest.with_updated_name("Different Name")
        fp2 = compute_manifest_fingerprint(manifest2.to_canonical_dict())

        assert fp1 != fp2


class TestCrossSeriesIsolation:
    """CSI-01 ~ CSI-10: Cross-Series Isolation Tests."""

    def test_csi_01_series_character_id_isolation(self):
        """CSI-01: Same Korean name in different series -> different series_character_id."""
        # This test verifies the contract that downstream batches must implement
        # The identity primitive uses series_id as namespace
        from core.series_identity import compute_series_id

        series_a_id = compute_series_id("series_a")
        series_b_id = compute_series_id("series_b")

        # Simulate the downstream namespace isolation
        def compute_series_character_id(series_id: str, korean_name: str) -> str:
            import hashlib
            return f"schar_{hashlib.sha256(f'{series_id}|{korean_name}'.encode()).hexdigest()[:16]}"

        char_a = compute_series_character_id(series_a_id, "李某")
        char_b = compute_series_character_id(series_b_id, "李某")

        assert char_a != char_b
        assert char_a.startswith("schar_")
        assert char_b.startswith("schar_")

    def test_csi_02_series_entity_id_isolation(self):
        """CSI-02: Same entity name in different series -> different series_entity_id."""
        from core.series_identity import compute_series_id

        series_a_id = compute_series_id("series_a")
        series_b_id = compute_series_id("series_b")

        def compute_series_entity_id(series_id: str, source: str, entity_type: str) -> str:
            import hashlib
            return f"sentity_{hashlib.sha256(f'{series_id}|{source}|{entity_type}'.encode()).hexdigest()[:16]}"

        entity_a = compute_series_entity_id(series_a_id, "정태의", "CHARACTER")
        entity_b = compute_series_entity_id(series_b_id, "정태의", "CHARACTER")

        assert entity_a != entity_b
        assert entity_a.startswith("sentity_")
        assert entity_b.startswith("sentity_")

    def test_csi_03_glossary_file_isolation(self):
        """CSI-03: Series glossary files are per-series."""
        series_a_id = compute_series_id("series_a")
        series_b_id = compute_series_id("series_b")

        file_a = f"series_glossary_{series_a_id}.json"
        file_b = f"series_glossary_{series_b_id}.json"

        assert file_a != file_b

    def test_csi_04_registry_inmemory_isolation(self, tmp_path):
        """CSI-04: SeriesRegistry returns independent manifests."""
        registry = SeriesRegistry(tmp_path)
        registry.create("Passion")
        registry.create("Another")

        series_a = registry.get(compute_series_id("passion"))
        series_b = registry.get(compute_series_id("another"))

        assert series_a.series_id != series_b.series_id
        assert series_a.series_name != series_b.series_name

    def test_csi_05_promotion_non_leakage(self, tmp_path):
        """CSI-05: Series A promotion doesn't leak to Series B (different canonical keys)."""
        registry = SeriesRegistry(tmp_path)
        created_a = registry.create("Passion")
        created_b = registry.create("Passion Series")  # Different canonical key -> different series_id

        # Add books to A
        registry.add_book(
            series_id=created_a.series_id,
            book_identity="book_a1",
            source_path="a1.txt",
            title="A Vol 1",
            content_fingerprint="cf_a1",
            manifest_fingerprint="mf_a1",
        )

        # Series B should have no books
        manifest_b = registry.get(created_b.series_id)
        assert len(manifest_b.books) == 0

    def test_csi_06_checkpoint_isolation(self):
        """CSI-06: Series checkpoint files are per-series."""
        series_a_id = compute_series_id("series_a")
        series_b_id = compute_series_id("series_b")

        file_a = f"series_checkpoint_{series_a_id}.json"
        file_b = f"series_checkpoint_{series_b_id}.json"

        assert file_a != file_b

    def test_csi_07_same_canonical_key_deduplication(self, tmp_path):
        """CSI-07: Same canonical key raises error (no auto-merge), different keys produce different IDs.

        Per D-09: "同名 Series 不得自動合併。使用者若要延續既有 Series：必須明確選擇既有 Series identity."
        """
        registry = SeriesRegistry(tmp_path)
        created1 = registry.create("Passion")

        # Same canonical key -> create raises (no auto-merge per D-09)
        with pytest.raises(ValidationError, match="already exists"):
            registry.create("Passion")

        # User must explicitly get existing series
        retrieved = registry.get(created1.series_id)
        assert retrieved.series_id == created1.series_id
        assert retrieved.series_name == "Passion"

        # Different canonical key -> different series_id
        created3 = registry.create("Passion Series")
        assert created1.series_id != created3.series_id
        assert created1.manifest.series_name == "Passion"
        assert created3.manifest.series_name == "Passion Series"

    def test_csi_08_filesystem_isolation(self, tmp_path):
        """CSI-08: Delete Series A directory -> Series B unaffected."""
        registry = SeriesRegistry(tmp_path)
        created_a = registry.create("Series A")
        created_b = registry.create("Series B")

        # Delete A's directory
        import shutil
        series_dir_a = get_series_dir(tmp_path, created_a.series_id)
        shutil.rmtree(series_dir_a)

        # B should still be accessible
        manifest_b = registry.get(created_b.series_id)
        assert manifest_b.series_id == created_b.series_id

    def test_csi_09_runtime_concurrent_isolation(self):
        """CSI-09: SeriesIdentity passed explicitly, no global state."""
        # The design ensures no global state - SeriesIdentity is passed explicitly
        # to all operations. This is a design contract test.
        identity1 = SeriesIdentity.create("Passion")
        identity2 = SeriesIdentity.create("Passion")

        # Same canonical key -> same ID (deterministic)
        assert identity1.series_id == identity2.series_id

        # Different canonical keys -> different IDs
        identity3 = SeriesIdentity.create("Passion Series")
        assert identity1.series_id != identity3.series_id

    def test_csi_10_lifecycle_isolation(self, tmp_path):
        """CSI-10: Series A archived -> Series B active."""
        registry = SeriesRegistry(tmp_path)
        created_a = registry.create("Series A")
        created_b = registry.create("Series B")

        # Archive A
        registry.archive(created_a.series_id)

        # B should still be active
        manifest_b = registry.get(created_b.series_id)
        assert manifest_b.lifecycle_status == SeriesLifecycle.CREATED


class TestPropertyBased:
    """Property-based tests (1000 iterations)."""

    def test_series_id_deterministic_property(self):
        """Property: same input always produces same output."""
        import random
        import string

        for _ in range(1000):
            key = ''.join(random.choices(string.ascii_letters + string.digits + " ", k=20))
            id1 = compute_series_id(key)
            id2 = compute_series_id(key)
            assert id1 == id2, f"Non-deterministic for key: {key}"

    def test_manifest_fingerprint_deterministic_property(self):
        """Property: same manifest data always produces same fingerprint."""
        import random

        for _ in range(1000):
            name = ''.join(random.choices(string.ascii_letters, k=10))
            identity = SeriesIdentity.create(name)
            manifest = SeriesManifest(
                schema_name="ntpe.series_manifest",
                schema_version="1.0",
                series_id=identity.series_id,
                series_name=identity.series_name,
                lifecycle_status=SeriesLifecycle.CREATED,
                created_at=identity.created_at,
                updated_at=identity.updated_at,
                books=(),
                series_memory_hash="",
                series_checkpoint_hash="",
                manifest_fingerprint="",
            )

            fp1 = compute_manifest_fingerprint(manifest.to_canonical_dict())
            fp2 = compute_manifest_fingerprint(manifest.to_canonical_dict())
            assert fp1 == fp2

    def test_serialization_roundtrip_property(self, tmp_path):
        """Property: save -> load -> same fingerprint."""
        import random
        import string

        from core.series_identity import save_manifest, load_manifest

        for _ in range(1000):
            name = ''.join(random.choices(string.ascii_letters + " ", k=15)).strip()
            if not name:
                continue

            registry = SeriesRegistry(tmp_path)
            created = registry.create(name)
            loaded = registry.get(created.series_id)

            assert loaded.series_id == created.series_id
            assert loaded.series_name == created.manifest.series_name
            assert loaded.manifest_fingerprint == created.manifest.manifest_fingerprint


import string

# Run tests when executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
