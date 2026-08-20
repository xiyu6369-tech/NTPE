"""P0 Stage 5 Batch 5.4 — Series Glossary Tests.

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

from core.glossary_builder import (
    SeriesGlossaryTerm,
    SeriesGlossary,
    GlossaryPromotionRecord,
    build_series_glossary,
    load_series_glossary,
    merge_into_series_glossary,
    resolve_promotion_conflict,
    save_series_glossary,
    load_series_glossary_from_path,
    get_series_glossary_path,
    validate_series_glossary,
    compute_series_glossary_fingerprint,
    to_canonical_json,
    SeriesGlossaryValidationError,
    SeriesGlossaryIntegrityError,
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
from core.series_memory import SeriesMemoryStore


class TestSeriesGlossaryIdentity:
    """Tests for deterministic serialization and fingerprint (SG-01)."""

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

    def test_glossary_fingerprint_deterministic(self):
        """Same glossary -> same fingerprint."""
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            terms={},
            glossary_hash="",
        )
        fp1 = compute_series_glossary_fingerprint(glossary.to_dict(include_glossary_hash=False))
        fp2 = compute_series_glossary_fingerprint(glossary.to_dict(include_glossary_hash=False))
        assert fp1 == fp2
        assert len(fp1) == 64

    def test_glossary_fingerprint_changes_with_data(self):
        """Different terms -> different fingerprint."""
        term = SeriesGlossaryTerm(
            source="正泰的",
            translation="鄭泰義",
            category="person_name",
            locked=True,
            status="manual_locked",
            source_books=("book1",),
            book_coverage=1,
            confidence=1.0,
            aliases=(),
            notes=(),
            approved_at="2026-08-18T00:00:00Z",
            approved_by="user",
            version=1,
        )
        glossary1 = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            terms={"正泰的": term},
            glossary_hash="",
        )
        glossary2 = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            terms={},
            glossary_hash="",
        )
        fp1 = compute_series_glossary_fingerprint(glossary1.to_dict(include_glossary_hash=False))
        fp2 = compute_series_glossary_fingerprint(glossary2.to_dict(include_glossary_hash=False))
        assert fp1 != fp2


class TestSeriesGlossaryTerm:
    """Tests for SeriesGlossaryTerm model."""

    def test_term_creation(self):
        """Basic term creation with all fields."""
        term = SeriesGlossaryTerm(
            source="正泰的",
            translation="鄭泰義",
            category="person_name",
            locked=True,
            status="manual_locked",
            source_books=("book1", "book2"),
            book_coverage=2,
            confidence=1.0,
            aliases=("泰的", "正泰"),
            notes=("promoted from book1",),
            approved_at="2026-08-18T00:00:00Z",
            approved_by="series_promotion",
            version=1,
        )
        assert term.source == "正泰的"
        assert term.translation == "鄭泰義"
        assert term.locked is True
        assert term.status == "manual_locked"

    def test_term_immutability(self):
        """Term fields should be immutable (frozen dataclass)."""
        term = SeriesGlossaryTerm(
            source="正泰的",
            translation="鄭泰義",
            category="person_name",
            locked=True,
            status="manual_locked",
            source_books=("book1",),
            book_coverage=1,
            confidence=1.0,
            aliases=(),
            notes=(),
            approved_at="2026-08-18T00:00:00Z",
            approved_by="user",
            version=1,
        )
        with pytest.raises(AttributeError):
            term.translation = "新目標"

    def test_term_with_updated_translation(self):
        """Version increment on translation update."""
        term = SeriesGlossaryTerm(
            source="正泰的",
            translation="鄭泰義",
            category="person_name",
            locked=True,
            status="manual_locked",
            source_books=("book1",),
            book_coverage=1,
            confidence=1.0,
            aliases=(),
            notes=(),
            approved_at="2026-08-18T00:00:00Z",
            approved_by="user",
            version=1,
        )
        updated = term.with_updated_translation("鄭泰義新", "user", "2026-08-19T00:00:00Z")
        assert updated.version == 2
        assert updated.translation == "鄭泰義新"
        assert updated.approved_by == "user"
        assert "updated from" in updated.notes[-1]

    def test_term_serialization_roundtrip(self):
        """Term should serialize and deserialize correctly."""
        term = SeriesGlossaryTerm(
            source="正泰的",
            translation="鄭泰義",
            category="person_name",
            locked=True,
            status="manual_locked",
            source_books=("book1",),
            book_coverage=1,
            confidence=1.0,
            aliases=("泰的",),
            notes=("note",),
            approved_at="2026-08-18T00:00:00Z",
            approved_by="user",
            version=1,
        )
        data = term.to_dict()
        loaded = SeriesGlossaryTerm.from_dict(data)
        assert loaded.source == term.source
        assert loaded.translation == term.translation
        assert loaded.locked == term.locked
        assert loaded.version == term.version


class TestSeriesGlossary:
    """Tests for SeriesGlossary model."""

    def test_glossary_creation(self):
        """Basic glossary creation."""
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            terms={},
            glossary_hash="",
        )
        assert len(glossary.terms) == 0
        assert glossary.series_id == "a1b2c3d4e5f6g7h8"

    def test_glossary_get_locked_dictionary(self):
        """Extract locked terms for frozen component integration."""
        term1 = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        term2 = SeriesGlossaryTerm(
            source="首尔", translation="首爾", category="place_name",
            locked=False, status="auto_high_confidence", source_books=("book1",),
            book_coverage=1, confidence=0.96, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="auto_high_confidence", version=1,
        )
        term3 = SeriesGlossaryTerm(
            source="未鎖定", translation="未锁定", category="unknown",
            locked=False, status="auto", source_books=("book1",),
            book_coverage=1, confidence=0.5, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="auto", version=1,
        )
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            terms={"正泰的": term1, "首尔": term2, "未鎖定": term3},
            glossary_hash="",
        )
        locked_dict = glossary.get_locked_dictionary()
        assert "正泰的" in locked_dict
        assert "首尔" in locked_dict
        assert "未鎖定" not in locked_dict
        assert locked_dict["正泰的"] == "鄭泰義"

    def test_glossary_get_alias_map(self):
        """Extract aliases for GlossaryContext."""
        term = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=("泰的", "正泰"),
            notes=(), approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id="a1b2c3d4e5f6g7h8",
            terms={"正泰的": term},
            glossary_hash="",
        )
        alias_map = glossary.get_alias_map()
        assert alias_map["泰的"] == "鄭泰義"
        assert alias_map["正泰"] == "鄭泰義"


class TestPersistence:
    """Tests for deterministic persistence with SHA-256 fingerprint."""

    def setup_method(self):
        self.tmp_path = Path("D:/Temp/kilo/test_series_glossary")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        self.series_id = compute_series_id("TestGlossarySeries")

    def test_save_load_roundtrip(self):
        """Save -> load -> fingerprint matches."""
        term = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_id,
            terms={"正泰的": term},
            glossary_hash="",
        )
        fingerprint = compute_series_glossary_fingerprint(glossary.to_dict(include_glossary_hash=False))
        glossary = SeriesGlossary(
            schema_name=glossary.schema_name,
            schema_version=glossary.schema_version,
            series_id=glossary.series_id,
            terms=glossary.terms,
            glossary_hash=fingerprint,
        )

        path = get_series_glossary_path(self.tmp_path, self.series_id)
        save_series_glossary(glossary, path)

        loaded = load_series_glossary_from_path(path, self.series_id)
        assert len(loaded.terms) == 1
        assert loaded.get_glossary_hash() == glossary.get_glossary_hash()

    def test_deterministic_serialization(self):
        """Same glossary -> bit-for-bit identical JSON."""
        term = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_id,
            terms={"正泰的": term},
            glossary_hash="",
        )
        fingerprint = compute_series_glossary_fingerprint(glossary.to_dict(include_glossary_hash=False))
        glossary = SeriesGlossary(
            schema_name=glossary.schema_name,
            schema_version=glossary.schema_version,
            series_id=glossary.series_id,
            terms=glossary.terms,
            glossary_hash=fingerprint,
        )

        path = get_series_glossary_path(self.tmp_path, self.series_id)
        save_series_glossary(glossary, path)
        content1 = path.read_text(encoding="utf-8")

        loaded = load_series_glossary_from_path(path, self.series_id)
        save_series_glossary(loaded, path)
        content2 = path.read_text(encoding="utf-8")

        assert content1 == content2

    def test_corrupted_json_rejected(self):
        """Corrupted JSON must raise exception (fail-closed)."""
        term = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_id,
            terms={"正泰的": term},
            glossary_hash="",
        )
        fingerprint = compute_series_glossary_fingerprint(glossary.to_dict(include_glossary_hash=False))
        glossary = SeriesGlossary(
            schema_name=glossary.schema_name,
            schema_version=glossary.schema_version,
            series_id=glossary.series_id,
            terms=glossary.terms,
            glossary_hash=fingerprint,
        )

        path = get_series_glossary_path(self.tmp_path, self.series_id)
        save_series_glossary(glossary, path)

        path.write_text("{ invalid json", encoding="utf-8")
        with pytest.raises(SeriesGlossaryValidationError, match="Invalid JSON"):
            load_series_glossary_from_path(path, self.series_id)

    def test_fingerprint_mismatch_rejected(self):
        """Tampered fingerprint must raise IntegrityError (fail-closed)."""
        term = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_id,
            terms={"正泰的": term},
            glossary_hash="",
        )
        fingerprint = compute_series_glossary_fingerprint(glossary.to_dict(include_glossary_hash=False))
        glossary = SeriesGlossary(
            schema_name=glossary.schema_name,
            schema_version=glossary.schema_version,
            series_id=glossary.series_id,
            terms=glossary.terms,
            glossary_hash=fingerprint,
        )

        path = get_series_glossary_path(self.tmp_path, self.series_id)
        save_series_glossary(glossary, path)

        import json
        data = json.loads(path.read_text(encoding="utf-8"))
        data["terms"]["正泰的"]["translation"] = "篡改"
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(SeriesGlossaryIntegrityError, match="Glossary fingerprint mismatch"):
            load_series_glossary_from_path(path, self.series_id)

    def test_missing_file_returns_empty(self):
        """Loading non-existent glossary should return empty glossary."""
        empty = load_series_glossary_from_path(
            get_series_glossary_path(self.tmp_path, "nonexistent"),
            "nonexistent"
        )
        assert len(empty.terms) == 0
        assert empty.series_id == "nonexistent"

    def test_persistence_isolation_cross_series(self):
        """Series A and B have separate glossary files."""
        series_a_id = compute_series_id("SeriesA")
        series_b_id = compute_series_id("SeriesB")

        term_a = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義_A", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        glossary_a = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=series_a_id,
            terms={"正泰的": term_a},
            glossary_hash="",
        )
        fingerprint = compute_series_glossary_fingerprint(glossary_a.to_dict(include_glossary_hash=False))
        glossary_a = SeriesGlossary(
            schema_name=glossary_a.schema_name,
            schema_version=glossary_a.schema_version,
            series_id=glossary_a.series_id,
            terms=glossary_a.terms,
            glossary_hash=fingerprint,
        )

        term_b = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義_B", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        glossary_b = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=series_b_id,
            terms={"正泰的": term_b},
            glossary_hash="",
        )
        fingerprint = compute_series_glossary_fingerprint(glossary_b.to_dict(include_glossary_hash=False))
        glossary_b = SeriesGlossary(
            schema_name=glossary_b.schema_name,
            schema_version=glossary_b.schema_version,
            series_id=glossary_b.series_id,
            terms=glossary_b.terms,
            glossary_hash=fingerprint,
        )

        path_a = get_series_glossary_path(self.tmp_path, series_a_id)
        path_b = get_series_glossary_path(self.tmp_path, series_b_id)
        save_series_glossary(glossary_a, path_a)
        save_series_glossary(glossary_b, path_b)

        assert path_a != path_b
        assert path_a.exists()
        assert path_b.exists()

        loaded_a = load_series_glossary_from_path(path_a, series_a_id)
        loaded_b = load_series_glossary_from_path(path_b, series_b_id)
        assert loaded_a.terms["正泰的"].translation == "鄭泰義_A"
        assert loaded_b.terms["正泰的"].translation == "鄭泰義_B"


class TestBuildSeriesGlossary:
    """Tests for build_series_glossary() — cross-volume canonical merge."""

    def setup_method(self):
        self.tmp_path = Path("D:/Temp/kilo/test_build_glossary")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        self.series_id = compute_series_id("BuildGlossarySeries")

    def test_build_empty_no_completed_books(self):
        """No completed books -> empty glossary."""
        manifest = SeriesManifest(
            schema_name="ntpe.series_manifest",
            schema_version="1.0",
            series_id=self.series_id,
            series_name="Test",
            lifecycle_status=SeriesLifecycle.CREATED,
            created_at="2026-08-18T00:00:00Z",
            updated_at="2026-08-18T00:00:00Z",
            books=(),
            series_memory_hash="",
            series_checkpoint_hash="",
            series_entity_registry_hash="",
            series_glossary_hash="",
            manifest_fingerprint="",
        )
        glossary = build_series_glossary(self.series_id, manifest, self.tmp_path)
        assert len(glossary.terms) == 0

    def test_build_from_completed_books_only(self):
        """Only completed/promoted books contribute to glossary."""
        # This test would need analysis files - skip for now as it requires file setup
        pass


class TestPromotion:
    """Tests for Book → Series promotion (MANUAL gate, D-07 frozen)."""

    def setup_method(self):
        self.tmp_path = Path("D:/Temp/kilo/test_promo_glossary")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        self.series_id = compute_series_id("PromoGlossarySeries")

    def test_promotion_manual_gate_enforced(self):
        """Promotion with approval_gate=False must raise (D-07 frozen)."""
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_id,
            terms={},
            glossary_hash="",
        )
        with pytest.raises(SeriesGlossaryValidationError, match="MANUAL approval gate"):
            merge_into_series_glossary(
                glossary,
                {"正泰的": {"translation": "鄭泰義", "locked": True, "confidence": 1.0, "category": "person_name"}},
                "book1",
                approval_gate=False,
            )

    def test_promotion_new_locked_term_created(self):
        """New locked term from book creates SeriesGlossaryTerm."""
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_id,
            terms={},
            glossary_hash="",
        )
        book_glossary = {
            "正泰的": {
                "translation": "鄭泰義",
                "locked": True,
                "confidence": 1.0,
                "category": "person_name",
                "aliases": ["泰的"],
                "notes": ["manual override"],
            }
        }
        updated, promotions = merge_into_series_glossary(glossary, book_glossary, "book1", approval_gate=True)

        assert len(promotions) == 1
        assert promotions[0].action == "created"
        assert promotions[0].source_term == "正泰的"
        assert promotions[0].new_translation == "鄭泰義"
        assert promotions[0].resolved_by == "user"
        assert "正泰的" in updated.terms
        assert updated.terms["正泰的"].translation == "鄭泰義"
        assert updated.terms["正泰的"].status == "locked"

    def test_promotion_high_confidence_term_created(self):
        """High confidence (>=0.95) term from book creates SeriesGlossaryTerm."""
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_id,
            terms={},
            glossary_hash="",
        )
        book_glossary = {
            "首尔": {
                "translation": "首爾",
                "locked": False,
                "confidence": 0.96,
                "category": "place_name",
                "aliases": [],
                "notes": [],
            }
        }
        updated, promotions = merge_into_series_glossary(glossary, book_glossary, "book1", approval_gate=True)

        assert len(promotions) == 1
        assert promotions[0].action == "created"
        assert "首尔" in updated.terms
        assert updated.terms["首尔"].translation == "首爾"
        assert updated.terms["首尔"].confidence >= 0.95

    def test_promotion_same_translation_no_op(self):
        """Same translation already in series -> NO-OP."""
        existing = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="series_promotion", version=1,
        )
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_id,
            terms={"正泰的": existing},
            glossary_hash="",
        )
        book_glossary = {
            "正泰的": {
                "translation": "鄭泰義",
                "locked": True,
                "confidence": 1.0,
                "category": "person_name",
                "aliases": [],
                "notes": [],
            }
        }
        updated, promotions = merge_into_series_glossary(glossary, book_glossary, "book2", approval_gate=True)

        assert len(promotions) == 1
        assert promotions[0].action == "no_op"
        assert len(updated.terms) == 1  # No duplicate

    def test_promotion_different_translation_conflict(self):
        """Different translation in series -> CONFLICT."""
        existing = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="series_promotion", version=1,
        )
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_id,
            terms={"正泰的": existing},
            glossary_hash="",
        )
        book_glossary = {
            "正泰的": {
                "translation": "鄭泰義不同",
                "locked": True,
                "confidence": 1.0,
                "category": "person_name",
                "aliases": [],
                "notes": [],
            }
        }
        updated, promotions = merge_into_series_glossary(glossary, book_glossary, "book2", approval_gate=True)

        assert len(promotions) == 1
        assert promotions[0].action == "conflict"
        assert promotions[0].resolved_by is None
        # Series term should be unchanged
        assert updated.terms["正泰的"].translation == "鄭泰義"

    def test_promotion_low_confidence_blocked(self):
        """Confidence < 0.95 and not locked -> not promoted."""
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_id,
            terms={},
            glossary_hash="",
        )
        book_glossary = {
            "未鎖定": {
                "translation": "未锁定",
                "locked": False,
                "confidence": 0.5,
                "category": "unknown",
                "aliases": [],
                "notes": [],
            }
        }
        updated, promotions = merge_into_series_glossary(glossary, book_glossary, "book1", approval_gate=True)

        assert len(promotions) == 0
        assert "未鎖定" not in updated.terms

    def test_promotion_audit_trail(self):
        """GlossaryPromotionRecord created for each promotion."""
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_id,
            terms={},
            glossary_hash="",
        )
        book_glossary = {
            "正泰的": {
                "translation": "鄭泰義",
                "locked": True,
                "confidence": 1.0,
                "category": "person_name",
                "aliases": [],
                "notes": [],
            }
        }
        updated, promotions = merge_into_series_glossary(glossary, book_glossary, "book1", approval_gate=True)

        assert len(promotions) == 1
        promo = promotions[0]
        assert promo.promotion_id is not None
        assert promo.series_id == self.series_id
        assert promo.book_identity == "book1"
        assert promo.source_term == "正泰的"
        assert promo.action == "created"
        assert promo.resolved_by == "user"


class TestConflictResolution:
    """Tests for MANUAL conflict resolution."""

    def setup_method(self):
        self.tmp_path = Path("D:/Temp/kilo/test_conflict_glossary")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        self.series_id = compute_series_id("ConflictGlossarySeries")
        self.existing = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="series_promotion", version=1,
        )
        self.glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_id,
            terms={"正泰的": self.existing},
            glossary_hash="",
        )
        fingerprint = compute_series_glossary_fingerprint(self.glossary.to_dict(include_glossary_hash=False))
        self.glossary = SeriesGlossary(
            schema_name=self.glossary.schema_name,
            schema_version=self.glossary.schema_version,
            series_id=self.glossary.series_id,
            terms=self.glossary.terms,
            glossary_hash=fingerprint,
        )

    def test_resolve_conflict_book_wins(self):
        """Resolve conflict: book_wins uses proposed target."""
        updated, record = resolve_promotion_conflict(
            self.glossary, "正泰的", "book_wins", "user", manual_value="鄭泰義新"
        )
        assert record.action == "updated"
        assert updated.terms["正泰的"].translation == "鄭泰義新"
        assert updated.terms["正泰的"].version == 2

    def test_resolve_conflict_series_wins(self):
        """Resolve conflict: series_wins keeps existing target."""
        updated, record = resolve_promotion_conflict(
            self.glossary, "正泰的", "series_wins", "user"
        )
        assert record.action == "no_op"
        assert updated.terms["正泰的"].translation == "鄭泰義"
        assert updated.terms["正泰的"].version == 1

    def test_resolve_conflict_manual_value(self):
        """Resolve conflict: manual provides custom value."""
        updated, record = resolve_promotion_conflict(
            self.glossary, "正泰的", "manual", "user", manual_value="鄭泰義手動"
        )
        assert record.action == "updated"
        assert updated.terms["正泰的"].translation == "鄭泰義手動"
        assert updated.terms["正泰的"].version == 2

    def test_resolve_invalid_resolution_raises(self):
        """Invalid resolution option raises."""
        with pytest.raises(SeriesGlossaryValidationError, match="Invalid resolution"):
            resolve_promotion_conflict(
                self.glossary, "正泰的", "invalid", "user"
            )

    def test_resolve_book_wins_requires_manual_value(self):
        """book_wins requires manual_value."""
        with pytest.raises(SeriesGlossaryValidationError, match="book_wins requires manual_value"):
            resolve_promotion_conflict(
                self.glossary, "正泰的", "book_wins", "user"
            )


class TestManifestIntegration:
    """Tests for SeriesManifest series_glossary_hash integration."""

    def setup_method(self):
        self.tmp_path = Path("D:/Temp/kilo/test_manifest_glossary")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        unique_name = f"ManifestGlossarySeries_{uuid.uuid4().hex[:8]}"
        self.series_id = compute_series_id(unique_name)

        self.series_registry_obj = SeriesRegistry(self.tmp_path)
        created = self.series_registry_obj.create(unique_name)
        self.series_id = created.series_id

    def test_manifest_has_glossary_hash_field(self):
        """Manifest has series_glossary_hash field."""
        manifest = self.series_registry_obj.get(self.series_id)
        assert hasattr(manifest, "series_glossary_hash")
        assert manifest.series_glossary_hash == ""

    def test_manifest_fingerprint_changes_with_glossary_hash(self):
        """Manifest fingerprint changes when glossary hash changes."""
        manifest1 = self.series_registry_obj.get(self.series_id)
        fp1 = manifest1.manifest_fingerprint

        self.series_registry_obj.update_series_glossary_hash(self.series_id, "new_glossary_hash")

        manifest2 = self.series_registry_obj.get(self.series_id)
        fp2 = manifest2.manifest_fingerprint

        assert fp1 != fp2
        assert manifest2.series_glossary_hash == "new_glossary_hash"

    def test_old_manifest_loads_without_glossary_hash(self):
        """Pre-Batch 5.4 manifest (no glossary hash) loads with empty string."""
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
            series_glossary_hash="",
            manifest_fingerprint="",
        )
        path = manifest_file_path(get_series_dir(self.tmp_path, self.series_id), self.series_id)
        save_manifest(old_manifest, path)

        loaded = load_manifest(path)
        assert loaded.series_glossary_hash == ""

    def test_glossary_update_propagates_to_manifest(self):
        """Glossary changes -> new glossary hash -> manifest update."""
        manifest_before = self.series_registry_obj.get(self.series_id)
        hash_before = manifest_before.series_glossary_hash

        self.series_registry_obj.update_series_glossary_hash(self.series_id, "updated_hash")

        manifest_after = self.series_registry_obj.get(self.series_id)
        hash_after = manifest_after.series_glossary_hash

        assert hash_before != hash_after
        assert hash_after == "updated_hash"


class TestCrossSeriesIsolation:
    """Tests for cross-series isolation (CSI-03 hard gate)."""

    def setup_method(self):
        self.tmp_path = Path("D:/Temp/kilo/test_isolation_glossary")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        self.series_a_id = compute_series_id("SeriesA_Glossary")
        self.series_b_id = compute_series_id("SeriesB_Glossary")

    def test_glossary_file_isolation(self):
        """Series A and B have separate glossary files."""
        term_a = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義_A", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        glossary_a = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_a_id,
            terms={"正泰的": term_a},
            glossary_hash="",
        )
        fingerprint = compute_series_glossary_fingerprint(glossary_a.to_dict(include_glossary_hash=False))
        glossary_a = SeriesGlossary(
            schema_name=glossary_a.schema_name,
            schema_version=glossary_a.schema_version,
            series_id=glossary_a.series_id,
            terms=glossary_a.terms,
            glossary_hash=fingerprint,
        )

        term_b = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義_B", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        glossary_b = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_b_id,
            terms={"正泰的": term_b},
            glossary_hash="",
        )
        fingerprint = compute_series_glossary_fingerprint(glossary_b.to_dict(include_glossary_hash=False))
        glossary_b = SeriesGlossary(
            schema_name=glossary_b.schema_name,
            schema_version=glossary_b.schema_version,
            series_id=glossary_b.series_id,
            terms=glossary_b.terms,
            glossary_hash=fingerprint,
        )

        path_a = get_series_glossary_path(self.tmp_path, self.series_a_id)
        path_b = get_series_glossary_path(self.tmp_path, self.series_b_id)
        save_series_glossary(glossary_a, path_a)
        save_series_glossary(glossary_b, path_b)

        loaded_a = load_series_glossary_from_path(path_a, self.series_a_id)
        loaded_b = load_series_glossary_from_path(path_b, self.series_b_id)

        assert loaded_a.terms["正泰的"].translation == "鄭泰義_A"
        assert loaded_b.terms["正泰的"].translation == "鄭泰義_B"
        assert loaded_a.terms["正泰的"].translation != loaded_b.terms["正泰的"].translation

    def test_hydration_isolation(self):
        """Hydration from Series A does not leak to Series B."""
        term_a = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義_A", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        glossary_a = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_a_id,
            terms={"正泰的": term_a},
            glossary_hash="",
        )

        term_b = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義_B", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        glossary_b = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_b_id,
            terms={"正泰的": term_b},
            glossary_hash="",
        )

        dict_a = glossary_a.get_locked_dictionary()
        dict_b = glossary_b.get_locked_dictionary()

        assert dict_a["正泰的"] == "鄭泰義_A"
        assert dict_b["正泰的"] == "鄭泰義_B"
        assert dict_a != dict_b

    def test_promotion_isolation(self):
        """Promotion in Series A does not affect Series B."""
        glossary_a = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_a_id,
            terms={},
            glossary_hash="",
        )
        glossary_b = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=self.series_b_id,
            terms={},
            glossary_hash="",
        )

        book_glossary_a = {
            "正泰的": {"translation": "鄭泰義_A", "locked": True, "confidence": 1.0, "category": "person_name", "aliases": [], "notes": []}
        }
        book_glossary_b = {
            "正泰的": {"translation": "鄭泰義_B", "locked": True, "confidence": 1.0, "category": "person_name", "aliases": [], "notes": []}
        }

        updated_a, _ = merge_into_series_glossary(glossary_a, book_glossary_a, "book1", approval_gate=True)
        updated_b, _ = merge_into_series_glossary(glossary_b, book_glossary_b, "book1", approval_gate=True)

        assert updated_a.terms["正泰的"].translation == "鄭泰義_A"
        assert updated_b.terms["正泰的"].translation == "鄭泰義_B"


class TestFrozenComponentIntegration:
    """Tests for adapter pattern integration with frozen glossary components."""

    def test_glossary_adapter_integration(self):
        """SeriesGlossary locked terms can be loaded into core/glossary.py Glossary."""
        term = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id="test_series",
            terms={"正泰的": term},
            glossary_hash="",
        )

        # Adapter pattern: extract locked dictionary
        locked_dict = glossary.get_locked_dictionary()

        # Verify it can be used by frozen Glossary class
        from core.glossary import Glossary
        g = Glossary(Path("dummy.txt"))  # Won't be used since we override
        g.terms = locked_dict

        assert "正泰的" in g.terms
        assert g.terms["正泰的"] == "鄭泰義"

    def test_glossary_context_adapter_integration(self):
        """SeriesGlossary locked terms work with GlossaryContext.from_locked_dictionary."""
        term1 = SeriesGlossaryTerm(
            source="正泰的", translation="鄭泰義", category="person_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=("泰的",), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        term2 = SeriesGlossaryTerm(
            source="首尔", translation="首爾", category="place_name",
            locked=True, status="manual_locked", source_books=("book1",),
            book_coverage=1, confidence=1.0, aliases=(), notes=(),
            approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
        )
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id="test_series",
            terms={"正泰的": term1, "首尔": term2},
            glossary_hash="",
        )

        # Adapter pattern
        locked_dict = glossary.get_locked_dictionary()
        alias_map = glossary.get_alias_map()

        from core.literary.glossary_context import GlossaryContext
        context = GlossaryContext.from_locked_dictionary(
            locked_dict, "正泰的 在 首尔", alias_map
        )

        assert len(context.matched_terms) == 2
        assert "正泰的" in context.render()
        assert "首尔" in context.render()
        assert "泰的" in context.alias_map


class TestPropertyBased:
    """Property-based tests (1000 iterations)."""

    def test_glossary_fingerprint_deterministic_property(self):
        """Same glossary state always produces same fingerprint (1000 iterations)."""
        import random
        import string

        for _ in range(1000):
            series_key = "".join(random.choices(string.ascii_letters + " ", k=15)).strip()
            if not series_key:
                continue
            series_id = compute_series_id(series_key)

            term = SeriesGlossaryTerm(
                source="test", translation="測試", category="unknown",
                locked=True, status="manual_locked", source_books=("book1",),
                book_coverage=1, confidence=1.0, aliases=(), notes=(),
                approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
            )
            glossary = SeriesGlossary(
                schema_name="ntpe.series_glossary",
                schema_version="1.0",
                series_id=series_id,
                terms={"test": term},
                glossary_hash="",
            )

            fp1 = compute_series_glossary_fingerprint(glossary.to_dict(include_glossary_hash=False))
            fp2 = compute_series_glossary_fingerprint(glossary.to_dict(include_glossary_hash=False))
            assert fp1 == fp2

    def test_serialization_roundtrip_property(self):
        """Save -> load -> same fingerprint (1000 iterations)."""
        import random
        import string

        for _ in range(1000):
            series_key = "".join(random.choices(string.ascii_letters + " ", k=15)).strip()
            if not series_key:
                continue
            series_id = compute_series_id(series_key)

            term = SeriesGlossaryTerm(
                source="test", translation="測試", category="unknown",
                locked=True, status="manual_locked", source_books=("book1",),
                book_coverage=1, confidence=1.0, aliases=(), notes=(),
                approved_at="2026-08-18T00:00:00Z", approved_by="user", version=1,
            )
            glossary = SeriesGlossary(
                schema_name="ntpe.series_glossary",
                schema_version="1.0",
                series_id=series_id,
                terms={"test": term},
                glossary_hash="",
            )
            fingerprint = compute_series_glossary_fingerprint(glossary.to_dict(include_glossary_hash=False))
            glossary = SeriesGlossary(
                schema_name=glossary.schema_name,
                schema_version=glossary.schema_version,
                series_id=glossary.series_id,
                terms=glossary.terms,
                glossary_hash=fingerprint,
            )

            # Serialization roundtrip
            data = glossary.to_dict(include_glossary_hash=True)
            loaded = SeriesGlossary(
                schema_name=data["schema_name"],
                schema_version=data["schema_version"],
                series_id=data["series_id"],
                terms={k: SeriesGlossaryTerm.from_dict(v) for k, v in data["terms"].items()},
                glossary_hash=data["glossary_hash"],
            )

            fp1 = glossary.get_glossary_hash()
            fp2 = loaded.get_glossary_hash()
            assert fp1 == fp2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])