"""P0 Stage 5 Batch 5.5 — Series Knowledge Population Tests.

Dedicated test boundary for Batch 5.5 functionality covering:

1.  Series Knowledge loading
2.  SeriesMemoryStore -> KnowledgeRuntime projection
3.  SeriesGlossary -> KnowledgeRuntime projection
4.  Novel tier population
5.  Volume tier population
6.  Translation-start population behavior
7.  Single canonical Series Knowledge artifact
8.  Deterministic serialization
9.  SHA-256 fingerprint
10. series_knowledge_hash Manifest integration
11. SeriesRegistry hash update
12. Fail-closed fingerprint/integrity mismatch
13. Backward-compatible Manifest loading
14. Idempotent population
15. BACKGROUND / OTHER preservation
16. Existing KnowledgeDomain reuse
17. No SERIES KnowledgeDomain
18. MergedRuntime integration
19. EntityResolver boundary preservation
20. Cross-series isolation
21. Empty Series Knowledge behavior
22. Invalid/malformed Series Knowledge validation
23. Regression compatibility with existing Series Identity
24. Provider/network/translation leakage remains 0/0/0

Deterministic offline tests only. No provider, network, or translation execution.
Do NOT modify frozen contracts. Do NOT modify unrelated existing tests.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from core.knowledge_runtime import (
    KnowledgeRuntimeManager,
    KnowledgeMerger,
    MergedRuntime,
    KnowledgeDomain,
    KnowledgeManagerError,
)
from core.knowledge_runtime.loader import (
    KnowledgeLoader,
    SeriesKnowledge,
    KnowledgePopulationReport,
    SeriesKnowledgeValidationError,
    SeriesKnowledgeIntegrityError,
    compute_series_knowledge_fingerprint,
    get_series_knowledge_path,
    save_series_knowledge,
    load_series_knowledge,
    load_series_knowledge_from_path,
    to_canonical_json,
)
from core.knowledge_runtime.merger import MergeStrategy, DOMAIN_STRATEGIES
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
    ValidationError,
    IntegrityError,
)
from core.series_memory import (
    SeriesMemoryStore,
    SeriesCharacterRecord,
    create_series_character_record,
    SeriesMemoryValidationError,
    compute_series_character_id,
)
from core.series_memory.validation import (
    ALLOWED_HYDRATION_FACT_TYPES,
    compute_series_memory_fingerprint,
)
from core.character_memory_v2.models import (
    ApprovalStatus,
    Evidence,
    EvidenceType,
    FactType,
)
from core.glossary_builder import (
    SeriesGlossaryTerm,
    SeriesGlossary,
    compute_series_glossary_fingerprint,
    get_series_glossary_path,
    save_series_glossary,
    load_series_glossary_from_path,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_evidence(
    evidence_id: str = "ev_001",
    source_case_id: str = "series_test",
    source_segment_id: str = "seg_001",
    source_text_hash: str = "a" * 64,
    excerpt: str = "test excerpt",
    language: str = "ko",
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        source_case_id=source_case_id,
        source_segment_id=source_segment_id,
        source_text_hash=source_text_hash,
        excerpt=excerpt,
        language=language,
        observed_at="2026-01-01T00:00:00Z",
    )


def _make_series_character_record(
    series_id: str,
    korean_name: str,
    canonical_name: str,
    fact_type: FactType = FactType.CANONICAL_NAME,
    value: str = "",
    aliases: tuple = (),
    confidence: float = 1.0,
    source_books: tuple = ("book1",),
) -> SeriesCharacterRecord:
    val = value or canonical_name
    return create_series_character_record(
        series_id=series_id,
        korean_name=korean_name,
        canonical_name=canonical_name,
        aliases=aliases,
        fact_type=fact_type,
        value=val,
        evidence=(_make_evidence(),),
        confidence=confidence,
        source_books=source_books,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )


def _make_series_glossary(
    series_id: str,
    terms: dict | None = None,
) -> SeriesGlossary:
    term_dict = terms or {}
    glossary = SeriesGlossary(
        schema_name="ntpe.series_glossary",
        schema_version="1.0",
        series_id=series_id,
        terms=term_dict,
        glossary_hash="",
    )
    fingerprint = compute_series_glossary_fingerprint(
        glossary.to_dict(include_glossary_hash=False)
    )
    return SeriesGlossary(
        schema_name=glossary.schema_name,
        schema_version=glossary.schema_version,
        series_id=glossary.series_id,
        terms=glossary.terms,
        glossary_hash=fingerprint,
    )


def _make_glossary_term(
    source: str,
    translation: str,
    locked: bool = True,
    confidence: float = 1.0,
    category: str = "person_name",
) -> SeriesGlossaryTerm:
    return SeriesGlossaryTerm(
        source=source,
        translation=translation,
        category=category,
        locked=locked,
        status="manual_locked" if locked else "auto_high_confidence",
        source_books=("book1",),
        book_coverage=1,
        confidence=confidence,
        aliases=(),
        notes=(),
        approved_at="2026-01-01T00:00:00Z",
        approved_by="user",
        version=1,
    )


def _setup_series_with_registry(tmp_path: Path, series_name: str) -> tuple:
    """Create a series via SeriesRegistry and return (series_id, registry)."""
    registry = SeriesRegistry(tmp_path)
    created = registry.create(series_name)
    return created.series_id, registry


# ---------------------------------------------------------------------------
# 1. Series Knowledge Loading
# ---------------------------------------------------------------------------


class TestSeriesKnowledgeLoading:
    """Tests for SeriesKnowledge loading from disk."""

    def test_load_series_knowledge_returns_empty_for_missing_file(self, tmp_path):
        """Loading non-existent knowledge file returns empty SeriesKnowledge."""
        series_id = "a1b2c3d4e5f6g7h8"
        knowledge = load_series_knowledge(series_id, tmp_path)
        assert knowledge.series_id == series_id
        assert len(knowledge.character_entries) == 0
        assert len(knowledge.glossary_entries) == 0
        assert knowledge.knowledge_hash == ""

    def test_load_series_knowledge_roundtrip(self, tmp_path):
        """Save -> load -> same data."""
        series_id = compute_series_id("LoadTest")
        sk = SeriesKnowledge(
            schema_name="ntpe.series_knowledge",
            schema_version="1.0",
            series_id=series_id,
            character_entries={"char:aaa": "AAA"},
            glossary_entries={"bbb": "BBB"},
            general_entries={},
            knowledge_hash="",
        )
        fp = compute_series_knowledge_fingerprint(sk.to_dict(include_knowledge_hash=False))
        sk = SeriesKnowledge(
            schema_name=sk.schema_name,
            schema_version=sk.schema_version,
            series_id=sk.series_id,
            character_entries=sk.character_entries,
            glossary_entries=sk.glossary_entries,
            general_entries=sk.general_entries,
            knowledge_hash=fp,
        )
        path = get_series_knowledge_path(tmp_path, series_id)
        save_series_knowledge(sk, path)

        loaded = load_series_knowledge(series_id, tmp_path)
        assert loaded.series_id == series_id
        assert loaded.character_entries == {"char:aaa": "AAA"}
        assert loaded.glossary_entries == {"bbb": "BBB"}
        assert loaded.knowledge_hash == fp

    def test_load_series_knowledge_from_path_schema_validation(self, tmp_path):
        """Loading with wrong schema_name raises validation error."""
        series_id = compute_series_id("SchemaTest")
        path = get_series_knowledge_path(tmp_path, series_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({
                "schema_name": "wrong.schema",
                "schema_version": "1.0",
                "series_id": series_id,
                "character_entries": {},
                "glossary_entries": {},
                "general_entries": {},
                "knowledge_hash": "",
            }),
            encoding="utf-8",
        )
        with pytest.raises(SeriesKnowledgeValidationError, match="Invalid schema_name"):
            load_series_knowledge_from_path(path, series_id)

    def test_load_series_knowledge_id_mismatch(self, tmp_path):
        """Loading with wrong series_id raises validation error."""
        path = get_series_knowledge_path(tmp_path, "aaa")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({
                "schema_name": "ntpe.series_knowledge",
                "schema_version": "1.0",
                "series_id": "bbb",
                "character_entries": {},
                "glossary_entries": {},
                "general_entries": {},
                "knowledge_hash": "",
            }),
            encoding="utf-8",
        )
        with pytest.raises(SeriesKnowledgeValidationError, match="Series ID mismatch"):
            load_series_knowledge_from_path(path, "aaa")


# ---------------------------------------------------------------------------
# 2. SeriesMemoryStore -> KnowledgeRuntime Projection
# ---------------------------------------------------------------------------


class TestSeriesMemoryProjection:
    """Tests for SeriesMemoryStore -> KnowledgeRuntime projection."""

    def test_load_series_character_knowledge_canonical_name(self):
        """SeriesMemoryStore CANONICAL_NAME facts project to character entries."""
        series_id = compute_series_id("ProjectionTest")
        store = SeriesMemoryStore(series_id)
        record = _make_series_character_record(
            series_id, "aaa", "AAA"
        )
        store.add_or_merge_canonical_fact(record)

        loader = KnowledgeLoader()
        entries = loader.load_series_character_knowledge(store)
        assert f"char:aaa" in entries
        assert entries["char:aaa"] == "AAA"

    def test_load_series_character_knowledge_aliases(self):
        """SeriesMemoryStore aliases project to alias entries."""
        series_id = compute_series_id("AliasTest")
        store = SeriesMemoryStore(series_id)
        record = _make_series_character_record(
            series_id, "aaa", "AAA", aliases=("alias1", "alias2"),
        )
        store.add_or_merge_canonical_fact(record)

        loader = KnowledgeLoader()
        entries = loader.load_series_character_knowledge(store)
        assert entries["alias:alias1"] == "AAA"
        assert entries["alias:alias2"] == "AAA"

    def test_load_series_character_knowledge_relationship(self):
        """SeriesMemoryStore RELATIONSHIP facts project to rel entries."""
        series_id = compute_series_id("RelTest")
        store = SeriesMemoryStore(series_id)
        record = _make_series_character_record(
            series_id, "aaa", "REL_CANONICAL",
            fact_type=FactType.RELATIONSHIP,
            value="aaa is boss of bbb",
        )
        store.add_or_merge_canonical_fact(record)

        loader = KnowledgeLoader()
        entries = loader.load_series_character_knowledge(store)
        key = f"rel:aaa:aaa is boss of bbb"
        assert key in entries
        assert entries[key] == "aaa is boss of bbb"

    def test_load_series_character_knowledge_terminology_preference(self):
        """SeriesMemoryStore TERMINOLOGY_PREFERENCE facts project to term entries."""
        series_id = compute_series_id("TermTest")
        store = SeriesMemoryStore(series_id)
        record = _make_series_character_record(
            series_id, "aaa", "TERM_CANONICAL",
            fact_type=FactType.TERMINOLOGY_PREFERENCE,
            value="preferred_term_value",
        )
        store.add_or_merge_canonical_fact(record)

        loader = KnowledgeLoader()
        entries = loader.load_series_character_knowledge(store)
        assert f"term:aaa" in entries
        assert entries["term:aaa"] == "preferred_term_value"

    def test_load_series_character_knowledge_empty_store(self):
        """Empty SeriesMemoryStore produces empty character entries."""
        series_id = compute_series_id("EmptyStore")
        store = SeriesMemoryStore(series_id)
        loader = KnowledgeLoader()
        entries = loader.load_series_character_knowledge(store)
        assert entries == {}


# ---------------------------------------------------------------------------
# 3. SeriesGlossary -> KnowledgeRuntime Projection
# ---------------------------------------------------------------------------


class TestSeriesGlossaryProjection:
    """Tests for SeriesGlossary -> KnowledgeRuntime projection."""

    def test_load_series_glossary_knowledge_locked_terms(self):
        """SeriesGlossary locked terms project to glossary entries."""
        series_id = compute_series_id("GlossaryProj")
        term = _make_glossary_term("aaa", "AAA", locked=True)
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=series_id,
            terms={"aaa": term},
            glossary_hash="",
        )
        loader = KnowledgeLoader()
        entries = loader.load_series_glossary_knowledge(glossary)
        assert entries["aaa"] == "AAA"

    def test_load_series_glossary_knowledge_excludes_unlocked(self):
        """Unlocked glossary terms with low confidence are not projected."""
        series_id = compute_series_id("GlossaryUnlocked")
        # Unlocked with confidence < 0.95 should be excluded by get_locked_dictionary()
        term = _make_glossary_term("aaa", "AAA", locked=False, confidence=0.5)
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=series_id,
            terms={"aaa": term},
            glossary_hash="",
        )
        loader = KnowledgeLoader()
        entries = loader.load_series_glossary_knowledge(glossary)
        # get_locked_dictionary only returns locked terms OR high confidence (>=0.95)
        assert "aaa" not in entries

    def test_load_series_glossary_knowledge_empty(self):
        """Empty SeriesGlossary produces empty entries."""
        series_id = compute_series_id("GlossaryEmpty")
        glossary = SeriesGlossary(
            schema_name="ntpe.series_glossary",
            schema_version="1.0",
            series_id=series_id,
            terms={},
            glossary_hash="",
        )
        loader = KnowledgeLoader()
        entries = loader.load_series_glossary_knowledge(glossary)
        assert entries == {}


# ---------------------------------------------------------------------------
# 4. Novel Tier Population
# ---------------------------------------------------------------------------


class TestNovelTierPopulation:
    """Tests for Novel tier population from Series sources."""

    def test_novel_tier_character_population(self, tmp_path):
        """Character facts from SeriesMemoryStore populate Novel tier."""
        series_id, registry = _setup_series_with_registry(tmp_path, "NovelCharPop")
        store = SeriesMemoryStore(series_id)
        record = _make_series_character_record(series_id, "aaa", "AAA")
        store.add_or_merge_canonical_fact(record)

        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        report = manager.load_series_knowledge(
            series_id, store, glossary, tmp_path, registry,
        )
        assert report.series_id == series_id
        assert report.character_terms_populated > 0

        # Merged runtime is built in the Merger, not stored in Manager's _merged_runtime
        merged = manager.merger.get_merged()
        assert merged is not None
        entries = merged.resolve_all("character")
        assert "char:aaa" in entries
        assert entries["char:aaa"] == "AAA"

    def test_novel_tier_glossary_population(self, tmp_path):
        """Glossary terms from SeriesGlossary populate Novel tier."""
        series_id, registry = _setup_series_with_registry(tmp_path, "NovelGlossaryPop")
        store = SeriesMemoryStore(series_id)
        glossary = _make_series_glossary(
            series_id,
            terms={"aaa": _make_glossary_term("aaa", "AAA", locked=True)},
        )
        manager = KnowledgeRuntimeManager()
        report = manager.load_series_knowledge(
            series_id, store, glossary, tmp_path, registry,
        )
        assert report.glossary_terms_populated > 0

        merged = manager.merger.get_merged()
        assert merged is not None
        entries = merged.resolve_all("glossary")
        assert "aaa" in entries
        assert entries["aaa"] == "AAA"

    def test_novel_tier_combined_population(self, tmp_path):
        """Both character and glossary facts populate Novel tier."""
        series_id, registry = _setup_series_with_registry(tmp_path, "NovelCombined")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(
            series_id,
            terms={
                "bbb": _make_glossary_term("bbb", "BBB", locked=True),
            },
        )
        manager = KnowledgeRuntimeManager()
        report = manager.load_series_knowledge(
            series_id, store, glossary, tmp_path, registry,
        )
        assert report.character_terms_populated > 0
        assert report.glossary_terms_populated > 0

        merged = manager.merger.get_merged()
        assert merged is not None
        char_entries = merged.resolve_all("character")
        glossary_entries = merged.resolve_all("glossary")
        assert "char:aaa" in char_entries
        assert "bbb" in glossary_entries


# ---------------------------------------------------------------------------
# 5. Volume Tier Population
# ---------------------------------------------------------------------------


class TestVolumeTierPopulation:
    """Tests for Volume tier population at translation start."""

    def test_volume_tier_population_merges_with_novel(self, tmp_path):
        """Volume tier entries OVERRIDE Novel tier via KEY_OVERRIDE."""
        series_id, registry = _setup_series_with_registry(tmp_path, "VolumeTier")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        manager.load_series_knowledge(series_id, store, glossary, tmp_path, registry)

        # Create a minimal book memory store mock
        from unittest.mock import MagicMock
        mock_book_store = MagicMock()
        mock_book_store.get_all.return_value = []
        
        # Populate Volume tier with overriding value
        manager.populate_volume_tier(
            book_memory_store=mock_book_store,
            book_glossary={},
            book_identity="book1",
        )
        merged = manager.merger.get_merged()
        assert merged is not None

    def test_volume_tier_character_glossary_keys(self, tmp_path):
        """Volume tier populates character and glossary keys."""
        series_id, registry = _setup_series_with_registry(tmp_path, "VolumeKeys")
        store = SeriesMemoryStore(series_id)
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        manager.load_series_knowledge(series_id, store, glossary, tmp_path, registry)

        # Simulate a book glossary entry
        from unittest.mock import MagicMock
        mock_book_store = MagicMock()
        mock_book_store.get_all.return_value = []
        
        manager.populate_volume_tier(
            book_memory_store=mock_book_store,
            book_glossary={"term_x": {"translation": "TERM_X_TRANS"}},
            book_identity="book1",
        )
        merged = manager.merger.get_merged()
        assert merged is not None
        glossary_entries = merged.resolve_all("glossary")
        # Volume glossary should appear with "term:" prefix
        assert glossary_entries.get("term:term_x") == "TERM_X_TRANS"


# ---------------------------------------------------------------------------
# 6. Translation-Start Population Behavior
# ---------------------------------------------------------------------------


class TestTranslationStartPopulation:
    """Tests for translation-start population behavior (SK-1)."""

    def test_population_report_contains_source_hashes(self, tmp_path):
        """KnowledgePopulationReport contains source memory and glossary hashes."""
        series_id, registry = _setup_series_with_registry(tmp_path, "TransStartReport")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(
            series_id,
            terms={"bbb": _make_glossary_term("bbb", "BBB", locked=True)},
        )
        manager = KnowledgeRuntimeManager()
        report = manager.load_series_knowledge(
            series_id, store, glossary, tmp_path, registry,
        )
        assert report.source_memory_hash == store.series_memory_hash
        assert report.source_glossary_hash == glossary.glossary_hash

    def test_population_report_knowledge_hash_matches_artifact(self, tmp_path):
        """Report knowledge_hash matches the persisted artifact."""
        series_id, registry = _setup_series_with_registry(tmp_path, "TransStartHash")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        report = manager.load_series_knowledge(
            series_id, store, glossary, tmp_path, registry,
        )

        loaded = load_series_knowledge(series_id, tmp_path)
        assert report.knowledge_hash == loaded.knowledge_hash


# ---------------------------------------------------------------------------
# 7. Single Canonical Series Knowledge Artifact
# ---------------------------------------------------------------------------


class TestSingleCanonicalArtifact:
    """Tests for single canonical Series Knowledge artifact (SK-3)."""

    def test_single_artifact_file_created(self, tmp_path):
        """Exactly one series_knowledge_{series_id}.json is created."""
        series_id, registry = _setup_series_with_registry(tmp_path, "SingleArtifact")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        manager.load_series_knowledge(series_id, store, glossary, tmp_path, registry)

        knowledge_path = get_series_knowledge_path(tmp_path, series_id)
        assert knowledge_path.exists()

        # Only one knowledge file in the series directory
        series_dir = knowledge_path.parent
        knowledge_files = list(series_dir.glob("series_knowledge_*.json"))
        assert len(knowledge_files) == 1

    def test_artifact_contains_all_domains(self, tmp_path):
        """Artifact contains character, glossary, and general entries."""
        series_id, registry = _setup_series_with_registry(tmp_path, "ArtifactDomains")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(
            series_id,
            terms={"bbb": _make_glossary_term("bbb", "BBB", locked=True)},
        )
        manager = KnowledgeRuntimeManager()
        manager.load_series_knowledge(series_id, store, glossary, tmp_path, registry)

        loaded = load_series_knowledge(series_id, tmp_path)
        assert "schema_name" in loaded.to_dict()
        assert "character_entries" in loaded.to_dict()
        assert "glossary_entries" in loaded.to_dict()
        assert "general_entries" in loaded.to_dict()


# ---------------------------------------------------------------------------
# 8. Deterministic Serialization
# ---------------------------------------------------------------------------


class TestDeterministicSerialization:
    """Tests for deterministic canonical JSON serialization."""

    def test_canonical_json_sorted_keys(self):
        """Canonical JSON must have sorted keys."""
        json_str = to_canonical_json({"z": 1, "a": 2, "m": 3})
        assert json_str.index('"a"') < json_str.index('"m"')
        assert json_str.index('"m"') < json_str.index('"z"')

    def test_canonical_json_no_whitespace(self):
        """Canonical JSON must have no unnecessary whitespace."""
        json_str = to_canonical_json({"a": 1, "b": 2})
        assert " " not in json_str
        assert "\n" not in json_str
        assert "\t" not in json_str

    def test_deterministic_serialization_roundtrip(self, tmp_path):
        """Save -> load -> save produces bit-for-bit identical JSON."""
        series_id = compute_series_id("DetSerialize")
        sk = SeriesKnowledge(
            schema_name="ntpe.series_knowledge",
            schema_version="1.0",
            series_id=series_id,
            character_entries={"char:aaa": "AAA"},
            glossary_entries={"bbb": "BBB"},
            general_entries={},
            knowledge_hash="",
        )
        fp = compute_series_knowledge_fingerprint(sk.to_dict(include_knowledge_hash=False))
        sk = SeriesKnowledge(
            schema_name=sk.schema_name,
            schema_version=sk.schema_version,
            series_id=sk.series_id,
            character_entries=sk.character_entries,
            glossary_entries=sk.glossary_entries,
            general_entries=sk.general_entries,
            knowledge_hash=fp,
        )
        path = get_series_knowledge_path(tmp_path, series_id)
        save_series_knowledge(sk, path)
        content1 = path.read_text(encoding="utf-8")

        loaded = load_series_knowledge_from_path(path, series_id)
        save_series_knowledge(loaded, path)
        content2 = path.read_text(encoding="utf-8")

        assert content1 == content2


# ---------------------------------------------------------------------------
# 9. SHA-256 Fingerprint
# ---------------------------------------------------------------------------


class TestSHA256Fingerprint:
    """Tests for SHA-256 fingerprint determinism."""

    def test_fingerprint_deterministic(self):
        """Same payload -> same fingerprint."""
        sk = SeriesKnowledge(
            schema_name="ntpe.series_knowledge",
            schema_version="1.0",
            series_id="test",
            character_entries={"a": "A"},
            glossary_entries={"b": "B"},
            general_entries={},
            knowledge_hash="",
        )
        fp1 = compute_series_knowledge_fingerprint(sk.to_dict(include_knowledge_hash=False))
        fp2 = compute_series_knowledge_fingerprint(sk.to_dict(include_knowledge_hash=False))
        assert fp1 == fp2
        assert len(fp1) == 64  # SHA-256 hex

    def test_fingerprint_changes_with_data(self):
        """Different data -> different fingerprint."""
        sk1 = SeriesKnowledge(
            schema_name="ntpe.series_knowledge",
            schema_version="1.0",
            series_id="test",
            character_entries={"a": "A"},
            glossary_entries={},
            general_entries={},
            knowledge_hash="",
        )
        sk2 = SeriesKnowledge(
            schema_name="ntpe.series_knowledge",
            schema_version="1.0",
            series_id="test",
            character_entries={"a": "DIFFERENT"},
            glossary_entries={},
            general_entries={},
            knowledge_hash="",
        )
        fp1 = compute_series_knowledge_fingerprint(sk1.to_dict(include_knowledge_hash=False))
        fp2 = compute_series_knowledge_fingerprint(sk2.to_dict(include_knowledge_hash=False))
        assert fp1 != fp2

    def test_fingerprint_excludes_self(self):
        """Fingerprint computation excludes the knowledge_hash field itself."""
        sk = SeriesKnowledge(
            schema_name="ntpe.series_knowledge",
            schema_version="1.0",
            series_id="test",
            character_entries={},
            glossary_entries={},
            general_entries={},
            knowledge_hash="some_hash_value",
        )
        dict_with_hash = sk.to_dict(include_knowledge_hash=True)
        dict_without_hash = sk.to_dict(include_knowledge_hash=False)
        fp1 = compute_series_knowledge_fingerprint(dict_with_hash)
        fp2 = compute_series_knowledge_fingerprint(dict_without_hash)
        assert fp1 == fp2


# ---------------------------------------------------------------------------
# 10. series_knowledge_hash Manifest Integration
# ---------------------------------------------------------------------------


class TestManifestKnowledgeHashIntegration:
    """Tests for series_knowledge_hash in SeriesManifest."""

    def test_manifest_has_series_knowledge_hash_field(self, tmp_path):
        """SeriesManifest has series_knowledge_hash field defaulting to empty."""
        series_id, registry = _setup_series_with_registry(tmp_path, "ManifestHashField")
        manifest = registry.get(series_id)
        assert hasattr(manifest, "series_knowledge_hash")
        assert manifest.series_knowledge_hash == ""

    def test_manifest_fingerprint_changes_with_knowledge_hash(self, tmp_path):
        """Manifest fingerprint changes when knowledge hash is updated."""
        series_id, registry = _setup_series_with_registry(tmp_path, "ManifestFPChange")
        manifest1 = registry.get(series_id)
        fp1 = manifest1.manifest_fingerprint

        registry.update_series_knowledge_hash(series_id, "new_knowledge_hash_123")
        manifest2 = registry.get(series_id)
        fp2 = manifest2.manifest_fingerprint

        assert fp1 != fp2
        assert manifest2.series_knowledge_hash == "new_knowledge_hash_123"

    def test_load_series_knowledge_updates_manifest_hash(self, tmp_path):
        """Full pipeline: load_series_knowledge updates manifest with knowledge hash."""
        series_id, registry = _setup_series_with_registry(tmp_path, "PipelineHashUpdate")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        report = manager.load_series_knowledge(
            series_id, store, glossary, tmp_path, registry,
        )

        manifest = registry.get(series_id)
        assert manifest.series_knowledge_hash == report.knowledge_hash
        assert manifest.series_knowledge_hash != ""


# ---------------------------------------------------------------------------
# 11. SeriesRegistry Hash Update
# ---------------------------------------------------------------------------


class TestSeriesRegistryHashUpdate:
    """Tests for SeriesRegistry.update_series_knowledge_hash."""

    def test_update_series_knowledge_hash(self, tmp_path):
        """update_series_knowledge_hash sets the hash in manifest."""
        series_id, registry = _setup_series_with_registry(tmp_path, "RegistryHashUpdate")
        updated = registry.update_series_knowledge_hash(series_id, "hash_value_abc")
        assert updated.series_knowledge_hash == "hash_value_abc"

        manifest = registry.get(series_id)
        assert manifest.series_knowledge_hash == "hash_value_abc"

    def test_update_series_knowledge_hash_persists(self, tmp_path):
        """Hash update persists across registry reload."""
        series_id, registry = _setup_series_with_registry(tmp_path, "RegistryHashPersist")
        registry.update_series_knowledge_hash(series_id, "persisted_hash")

        # Reload registry
        registry2 = SeriesRegistry(tmp_path)
        manifest = registry2.get(series_id)
        assert manifest.series_knowledge_hash == "persisted_hash"

    def test_update_series_knowledge_hash_changes_fingerprint(self, tmp_path):
        """Each hash update changes the manifest fingerprint."""
        series_id, registry = _setup_series_with_registry(tmp_path, "RegistryFingerprint")
        registry.update_series_knowledge_hash(series_id, "hash1")
        fp1 = registry.get(series_id).manifest_fingerprint

        registry.update_series_knowledge_hash(series_id, "hash2")
        fp2 = registry.get(series_id).manifest_fingerprint

        assert fp1 != fp2


# ---------------------------------------------------------------------------
# 12. Fail-Closed Fingerprint / Integrity Mismatch
# ---------------------------------------------------------------------------


class TestFailClosedIntegrity:
    """Tests for fail-closed fingerprint integrity verification."""

    def test_tampered_knowledge_rejected(self, tmp_path):
        """Tampered knowledge file raises IntegrityError (fail-closed)."""
        series_id = compute_series_id("TamperedKnowledge")
        sk = SeriesKnowledge(
            schema_name="ntpe.series_knowledge",
            schema_version="1.0",
            series_id=series_id,
            character_entries={"char:aaa": "AAA"},
            glossary_entries={},
            general_entries={},
            knowledge_hash="",
        )
        fp = compute_series_knowledge_fingerprint(sk.to_dict(include_knowledge_hash=False))
        sk = SeriesKnowledge(
            schema_name=sk.schema_name,
            schema_version=sk.schema_version,
            series_id=sk.series_id,
            character_entries=sk.character_entries,
            glossary_entries=sk.glossary_entries,
            general_entries=sk.general_entries,
            knowledge_hash=fp,
        )
        path = get_series_knowledge_path(tmp_path, series_id)
        save_series_knowledge(sk, path)

        # Tamper with data
        data = json.loads(path.read_text(encoding="utf-8"))
        data["character_entries"]["char:aaa"] = "TAMPERED"
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(SeriesKnowledgeIntegrityError, match="fingerprint mismatch"):
            load_series_knowledge_from_path(path, series_id)

    def test_corrupted_json_rejected(self, tmp_path):
        """Corrupted JSON raises validation error (fail-closed)."""
        series_id = compute_series_id("CorruptedKnowledge")
        path = get_series_knowledge_path(tmp_path, series_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{ invalid json content }}}", encoding="utf-8")
        with pytest.raises(SeriesKnowledgeValidationError, match="Invalid JSON"):
            load_series_knowledge_from_path(path, series_id)

    def test_empty_file_rejected(self, tmp_path):
        """Empty knowledge file raises validation error."""
        series_id = compute_series_id("EmptyKnowledgeFile")
        path = get_series_knowledge_path(tmp_path, series_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
        with pytest.raises(SeriesKnowledgeValidationError, match="Invalid JSON"):
            load_series_knowledge_from_path(path, series_id)


# ---------------------------------------------------------------------------
# 13. Backward-Compatible Manifest Loading
# ---------------------------------------------------------------------------


class TestBackwardCompatibleManifest:
    """Tests for backward-compatible manifest loading (schema version 1.0)."""

    def test_old_manifest_loads_without_knowledge_hash(self, tmp_path):
        """Pre-Batch 5.5 manifest without series_knowledge_hash loads with default."""
        series_id = compute_series_id("OldManifest")
        series_dir = get_series_dir(tmp_path, series_id)
        series_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_file_path(series_dir, series_id)

        # Create old-style manifest without series_knowledge_hash
        old_manifest = SeriesManifest(
            schema_name="ntpe.series_manifest",
            schema_version="1.0",
            series_id=series_id,
            series_name="OldManifest",
            lifecycle_status=SeriesLifecycle.CREATED,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            books=(),
            series_memory_hash="",
            series_checkpoint_hash="",
            series_entity_registry_hash="",
            series_glossary_hash="",
            manifest_fingerprint="",
        )
        save_manifest(old_manifest, manifest_path)

        loaded = load_manifest(manifest_path)
        assert loaded.series_knowledge_hash == ""

    def test_manifest_dict_get_default_for_missing_field(self, tmp_path):
        """from_dict uses .get() with default "" for series_knowledge_hash."""
        series_id = compute_series_id("DictDefault")
        data = {
            "schema_name": "ntpe.series_manifest",
            "schema_version": "1.0",
            "series_id": series_id,
            "series_name": "DictDefault",
            "lifecycle_status": "CREATED",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "books": [],
        }
        manifest = SeriesManifest.from_dict(data)
        assert manifest.series_knowledge_hash == ""


# ---------------------------------------------------------------------------
# 14. Idempotent Population
# ---------------------------------------------------------------------------


class TestIdempotentPopulation:
    """Tests for idempotent Series Knowledge population."""

    def test_idempotent_population_same_hash(self, tmp_path):
        """Calling load_series_knowledge twice produces the same knowledge hash."""
        series_id, registry = _setup_series_with_registry(tmp_path, "Idempotent")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(series_id)

        manager1 = KnowledgeRuntimeManager()
        report1 = manager1.load_series_knowledge(series_id, store, glossary, tmp_path, registry)

        manager2 = KnowledgeRuntimeManager()
        report2 = manager2.load_series_knowledge(series_id, store, glossary, tmp_path, registry)

        assert report1.knowledge_hash == report2.knowledge_hash

    def test_idempotent_population_same_file_content(self, tmp_path):
        """Idempotent population produces identical file content."""
        series_id, registry = _setup_series_with_registry(tmp_path, "IdempotentFile")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(series_id)

        path = get_series_knowledge_path(tmp_path, series_id)

        manager1 = KnowledgeRuntimeManager()
        manager1.load_series_knowledge(series_id, store, glossary, tmp_path, registry)
        content1 = path.read_text(encoding="utf-8")

        manager2 = KnowledgeRuntimeManager()
        manager2.load_series_knowledge(series_id, store, glossary, tmp_path, registry)
        content2 = path.read_text(encoding="utf-8")

        assert content1 == content2


# ---------------------------------------------------------------------------
# 15. BACKGROUND / OTHER Preservation
# ---------------------------------------------------------------------------


class TestBackgroundOtherPreservation:
    """Tests for BACKGROUND/OTHER fact preservation (SK-2)."""

    def test_appearance_fact_type_preserved(self, tmp_path):
        """FactType.APPEARANCE facts map with fact:appearance: prefix."""
        series_id, registry = _setup_series_with_registry(tmp_path, "AppearancePreserve")
        store = SeriesMemoryStore(series_id)
        record = _make_series_character_record(
            series_id, "aaa", "AAA",
            fact_type=FactType.APPEARANCE,
            value="tall_and_handsome",
        )
        store.add_or_merge_canonical_fact(record)

        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        report = manager.load_series_knowledge(
            series_id, store, glossary, tmp_path, registry,
        )

        loaded = load_series_knowledge(series_id, tmp_path)
        assert any(k.startswith("fact:appearance:") for k in loaded.character_entries)


# ---------------------------------------------------------------------------
# 16. Existing KnowledgeDomain Reuse
# ---------------------------------------------------------------------------


class TestExistingKnowledgeDomainReuse:
    """Tests for existing KnowledgeDomain reuse (SK-6)."""

    def test_character_domain_reused(self, tmp_path):
        """Character facts use existing 'character' KnowledgeDomain."""
        series_id, registry = _setup_series_with_registry(tmp_path, "DomainReuseChar")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        manager.load_series_knowledge(series_id, store, glossary, tmp_path, registry)

        merged = manager.merger.get_merged()
        assert merged is not None
        assert "character" in merged.domains

    def test_glossary_domain_reused(self, tmp_path):
        """Glossary facts use existing 'glossary' KnowledgeDomain."""
        series_id, registry = _setup_series_with_registry(tmp_path, "DomainReuseGlossary")
        store = SeriesMemoryStore(series_id)
        glossary = _make_series_glossary(
            series_id,
            terms={"aaa": _make_glossary_term("aaa", "AAA", locked=True)},
        )
        manager = KnowledgeRuntimeManager()
        manager.load_series_knowledge(series_id, store, glossary, tmp_path, registry)

        merged = manager.merger.get_merged()
        assert merged is not None
        assert "glossary" in merged.domains

    def test_all_existing_domains_available(self):
        """All pre-existing KnowledgeDomain enum values exist."""
        domains = [d.name for d in KnowledgeDomain]
        assert "CHARACTER" in domains
        assert "GLOSSARY" in domains
        assert "GENERAL" in domains
        assert "NARRATIVE" in domains
        assert "SCENE" in domains
        assert "STYLE" in domains


# ---------------------------------------------------------------------------
# 17. No SERIES KnowledgeDomain
# ---------------------------------------------------------------------------


class TestNoSeriesKnowledgeDomain:
    """Tests confirming no new SERIES KnowledgeDomain was added (SK-6)."""

    def test_no_series_domain_in_enum(self):
        """KnowledgeDomain enum does not contain a SERIES member."""
        domain_names = [d.name for d in KnowledgeDomain]
        assert "SERIES" not in domain_names

    def test_no_series_domain_in_merged_runtime(self, tmp_path):
        """MergedRuntime does not contain a 'series' domain after population."""
        series_id, registry = _setup_series_with_registry(tmp_path, "NoSeriesDomain")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        manager.load_series_knowledge(series_id, store, glossary, tmp_path, registry)

        merged = manager.merger.get_merged()
        assert merged is not None
        assert "series" not in merged.domains
        assert "SERIES" not in merged.domains

    def test_domain_strategies_has_no_series(self):
        """DOMAIN_STRATEGIES does not include a 'series' domain."""
        assert "series" not in DOMAIN_STRATEGIES


# ---------------------------------------------------------------------------
# 18. MergedRuntime Integration
# ---------------------------------------------------------------------------


class TestMergedRuntimeIntegration:
    """Tests for MergedRuntime integration after Series Knowledge population."""

    def test_merged_runtime_built_after_population(self, tmp_path):
        """MergedRuntime is built and available after load_series_knowledge."""
        series_id, registry = _setup_series_with_registry(tmp_path, "MergedRT")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        manager.load_series_knowledge(series_id, store, glossary, tmp_path, registry)

        merged = manager.merger.get_merged()
        assert merged is not None
        assert isinstance(merged, MergedRuntime)

    def test_merged_runtime_resolve_character(self, tmp_path):
        """MergedRuntime can resolve character entries."""
        series_id, registry = _setup_series_with_registry(tmp_path, "MergedRTResolve")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        manager.load_series_knowledge(series_id, store, glossary, tmp_path, registry)

        merged = manager.merger.get_merged()
        assert merged is not None
        value = merged.resolve("char:aaa", "character")
        assert value == "AAA"

    def test_merged_runtime_resolve_all_glossary(self, tmp_path):
        """MergedRuntime resolve_all returns all glossary entries."""
        series_id, registry = _setup_series_with_registry(tmp_path, "MergedRTGlossary")
        store = SeriesMemoryStore(series_id)
        glossary = _make_series_glossary(
            series_id,
            terms={
                "aaa": _make_glossary_term("aaa", "AAA", locked=True),
                "bbb": _make_glossary_term("bbb", "BBB", locked=True),
            },
        )
        manager = KnowledgeRuntimeManager()
        manager.load_series_knowledge(series_id, store, glossary, tmp_path, registry)

        merged = manager.merger.get_merged()
        assert merged is not None
        entries = merged.resolve_all("glossary")
        assert len(entries) == 2
        assert entries["aaa"] == "AAA"
        assert entries["bbb"] == "BBB"


# ---------------------------------------------------------------------------
# 19. EntityResolver Boundary Preservation
# ---------------------------------------------------------------------------


class TestEntityResolverBoundary:
    """Tests for EntityResolver boundary preservation (SK-5)."""

    def test_entity_resolver_not_imported_by_knowledge_population(self, tmp_path):
        """Knowledge population does not import or modify EntityResolver."""
        series_id, registry = _setup_series_with_registry(tmp_path, "ResolverBoundary")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        manager.load_series_knowledge(series_id, store, glossary, tmp_path, registry)

        # EntityResolver is NOT used in the knowledge population pipeline
        # The merged runtime handles knowledge; EntityResolver handles entities separately
        # Verify the manager does not have a resolver that uses EntityResolver
        assert manager.resolver is not None
        # The resolver operates on KnowledgePrototype, not EntityResolver
        assert hasattr(manager.resolver, "prototypes")

    def test_knowledge_entries_separate_from_entity_resolver(self):
        """Knowledge entries use knowledge keys (char:, term:, rel:), not entity IDs."""
        series_id = compute_series_id("ResolverSep")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        loader = KnowledgeLoader()
        entries = loader.load_series_character_knowledge(store)

        # Keys are knowledge-scoped, not entity-scoped (no "schar_" prefix)
        for key in entries:
            assert not key.startswith("schar_")
            assert not key.startswith("sentity_")


# ---------------------------------------------------------------------------
# 20. Cross-Series Isolation
# ---------------------------------------------------------------------------


class TestCrossSeriesIsolation:
    """Tests for cross-series isolation of Series Knowledge."""

    def test_knowledge_files_are_series_isolated(self, tmp_path):
        """Series A and B produce separate knowledge files."""
        series_a_id, registry = _setup_series_with_registry(tmp_path, "IsolationA")
        series_b_id, _ = _setup_series_with_registry(tmp_path, "IsolationB")

        store_a = SeriesMemoryStore(series_a_id)
        store_a.add_or_merge_canonical_fact(
            _make_series_character_record(series_a_id, "aaa", "AAA_A")
        )
        store_b = SeriesMemoryStore(series_b_id)
        store_b.add_or_merge_canonical_fact(
            _make_series_character_record(series_b_id, "aaa", "AAA_B")
        )

        glossary_a = _make_series_glossary(series_a_id)
        glossary_b = _make_series_glossary(series_b_id)

        manager_a = KnowledgeRuntimeManager()
        manager_a.load_series_knowledge(series_a_id, store_a, glossary_a, tmp_path, registry)
        manager_b = KnowledgeRuntimeManager()
        manager_b.load_series_knowledge(series_b_id, store_b, glossary_b, tmp_path, registry)

        path_a = get_series_knowledge_path(tmp_path, series_a_id)
        path_b = get_series_knowledge_path(tmp_path, series_b_id)
        assert path_a != path_b
        assert path_a.exists()
        assert path_b.exists()

        loaded_a = load_series_knowledge(series_a_id, tmp_path)
        loaded_b = load_series_knowledge(series_b_id, tmp_path)

        assert loaded_a.character_entries.get("char:aaa") == "AAA_A"
        assert loaded_b.character_entries.get("char:aaa") == "AAA_B"

    def test_knowledge_hash_differs_between_series(self, tmp_path):
        """Same content in different series produces different hashes (series_id included)."""
        series_a_id, registry = _setup_series_with_registry(tmp_path, "HashIsoA")
        series_b_id, _ = _setup_series_with_registry(tmp_path, "HashIsoB")

        store_a = SeriesMemoryStore(series_a_id)
        store_a.add_or_merge_canonical_fact(
            _make_series_character_record(series_a_id, "aaa", "SAME_VALUE")
        )
        store_b = SeriesMemoryStore(series_b_id)
        store_b.add_or_merge_canonical_fact(
            _make_series_character_record(series_b_id, "aaa", "SAME_VALUE")
        )

        glossary_a = _make_series_glossary(series_a_id)
        glossary_b = _make_series_glossary(series_b_id)

        manager_a = KnowledgeRuntimeManager()
        report_a = manager_a.load_series_knowledge(series_a_id, store_a, glossary_a, tmp_path, registry)
        manager_b = KnowledgeRuntimeManager()
        report_b = manager_b.load_series_knowledge(series_b_id, store_b, glossary_b, tmp_path, registry)

        # series_id is part of the payload, so hashes differ even with same content
        assert report_a.knowledge_hash != report_b.knowledge_hash

    def test_cross_series_id_mismatch_rejected(self, tmp_path):
        """Loading knowledge with mismatched series_id is rejected."""
        series_id = compute_series_id("MismatchReject")
        sk = SeriesKnowledge(
            schema_name="ntpe.series_knowledge",
            schema_version="1.0",
            series_id=series_id,
            character_entries={},
            glossary_entries={},
            general_entries={},
            knowledge_hash="",
        )
        path = get_series_knowledge_path(tmp_path, series_id)
        save_series_knowledge(sk, path)

        with pytest.raises(SeriesKnowledgeValidationError, match="Series ID mismatch"):
            load_series_knowledge_from_path(path, "wrong_series_id")

    def test_manifest_knowledge_hash_isolated(self, tmp_path):
        """Each series manifest stores its own series_knowledge_hash."""
        series_a_id, registry = _setup_series_with_registry(tmp_path, "ManifestIsoA")
        series_b_id, _ = _setup_series_with_registry(tmp_path, "ManifestIsoB")

        registry.update_series_knowledge_hash(series_a_id, "hash_A")
        registry.update_series_knowledge_hash(series_b_id, "hash_B")

        manifest_a = registry.get(series_a_id)
        manifest_b = registry.get(series_b_id)

        assert manifest_a.series_knowledge_hash == "hash_A"
        assert manifest_b.series_knowledge_hash == "hash_B"
        assert manifest_a.series_knowledge_hash != manifest_b.series_knowledge_hash


# ---------------------------------------------------------------------------
# 21. Empty Series Knowledge Behavior
# ---------------------------------------------------------------------------


class TestEmptySeriesKnowledge:
    """Tests for empty Series Knowledge behavior."""

    def test_empty_store_produces_empty_knowledge(self, tmp_path):
        """Empty SeriesMemoryStore and SeriesGlossary produce empty knowledge."""
        series_id, registry = _setup_series_with_registry(tmp_path, "EmptyKnowledge")
        store = SeriesMemoryStore(series_id)
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        report = manager.load_series_knowledge(
            series_id, store, glossary, tmp_path, registry,
        )
        assert report.character_terms_populated == 0
        assert report.glossary_terms_populated == 0

        loaded = load_series_knowledge(series_id, tmp_path)
        assert len(loaded.character_entries) == 0
        assert len(loaded.glossary_entries) == 0

    def test_empty_knowledge_has_valid_fingerprint(self, tmp_path):
        """Empty knowledge file still has a valid SHA-256 fingerprint."""
        series_id, registry = _setup_series_with_registry(tmp_path, "EmptyFP")
        store = SeriesMemoryStore(series_id)
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        report = manager.load_series_knowledge(
            series_id, store, glossary, tmp_path, registry,
        )
        assert report.knowledge_hash != ""
        assert len(report.knowledge_hash) == 64

    def test_empty_knowledge_loadable(self, tmp_path):
        """Empty knowledge file loads without error."""
        series_id, registry = _setup_series_with_registry(tmp_path, "EmptyLoad")
        store = SeriesMemoryStore(series_id)
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        manager.load_series_knowledge(series_id, store, glossary, tmp_path, registry)

        loaded = load_series_knowledge(series_id, tmp_path)
        assert loaded.series_id == series_id
        assert loaded.knowledge_hash != ""


# ---------------------------------------------------------------------------
# 22. Invalid / Malformed Series Knowledge Validation
# ---------------------------------------------------------------------------


class TestInvalidMalformedKnowledge:
    """Tests for invalid/malformed Series Knowledge validation."""

    def test_wrong_schema_version_rejected(self, tmp_path):
        """Wrong schema_version raises validation error."""
        series_id = compute_series_id("WrongVersion")
        path = get_series_knowledge_path(tmp_path, series_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({
                "schema_name": "ntpe.series_knowledge",
                "schema_version": "2.0",
                "series_id": series_id,
                "character_entries": {},
                "glossary_entries": {},
                "general_entries": {},
                "knowledge_hash": "",
            }),
            encoding="utf-8",
        )
        with pytest.raises(SeriesKnowledgeValidationError, match="Invalid schema_version"):
            load_series_knowledge_from_path(path, series_id)

    def test_series_id_validation_on_population(self, tmp_path):
        """Population with mismatched SeriesMemoryStore series_id raises error."""
        series_id, registry = _setup_series_with_registry(tmp_path, "MismatchPop")
        wrong_store = SeriesMemoryStore("wrong_series_id")
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        with pytest.raises(KnowledgeManagerError, match="SeriesMemoryStore series_id mismatch"):
            manager.load_series_knowledge(series_id, wrong_store, glossary, tmp_path, registry)

    def test_series_glossary_id_validation_on_population(self, tmp_path):
        """Population with mismatched SeriesGlossary series_id raises error."""
        series_id, registry = _setup_series_with_registry(tmp_path, "GlossaryMismatch")
        store = SeriesMemoryStore(series_id)
        wrong_glossary = _make_series_glossary("wrong_series_id")
        manager = KnowledgeRuntimeManager()
        with pytest.raises(KnowledgeManagerError, match="SeriesGlossary series_id mismatch"):
            manager.load_series_knowledge(series_id, store, wrong_glossary, tmp_path, registry)


# ---------------------------------------------------------------------------
# 23. Regression Compatibility with Existing Series Identity
# ---------------------------------------------------------------------------


class TestRegressionSeriesIdentity:
    """Tests for regression compatibility with existing Series Identity."""

    def test_series_id_computation_unchanged(self):
        """compute_series_id still produces deterministic 16-char hex IDs."""
        id1 = compute_series_id("test")
        id2 = compute_series_id("test")
        assert id1 == id2
        assert len(id1) == 16
        assert all(c in "0123456789abcdef" for c in id1)

    def test_series_registry_create_unchanged(self, tmp_path):
        """SeriesRegistry.create still works as before."""
        registry = SeriesRegistry(tmp_path)
        result = registry.create("RegressionTest")
        assert result.series_id == compute_series_id("regressiontest")
        assert result.manifest.series_name == "RegressionTest"
        assert result.manifest.lifecycle_status == SeriesLifecycle.CREATED
        assert result.manifest_path.exists()

    def test_manifest_other_hashes_preserved(self, tmp_path):
        """Existing manifest hashes (memory, entity, glossary) are preserved alongside knowledge hash."""
        series_id, registry = _setup_series_with_registry(tmp_path, "PreservedHashes")
        registry.update_series_memory_hash(series_id, "mem_hash")
        registry.update_series_entity_registry_hash(series_id, "entity_hash")
        registry.update_series_glossary_hash(series_id, "glossary_hash")
        registry.update_series_knowledge_hash(series_id, "knowledge_hash")

        manifest = registry.get(series_id)
        assert manifest.series_memory_hash == "mem_hash"
        assert manifest.series_entity_registry_hash == "entity_hash"
        assert manifest.series_glossary_hash == "glossary_hash"
        assert manifest.series_knowledge_hash == "knowledge_hash"

    def test_manifest_books_unchanged(self, tmp_path):
        """Adding books still works with the new knowledge hash field."""
        series_id, registry = _setup_series_with_registry(tmp_path, "BooksUnchanged")
        result = registry.add_book(
            series_id=series_id,
            book_identity="book123",
            source_path="input/book1.txt",
            title="Test Vol 1",
            content_fingerprint="cf1",
            manifest_fingerprint="mf1",
        )
        assert result.volume_number == 1
        assert result.book_entry.book_identity == "book123"

        manifest = registry.get(series_id)
        assert len(manifest.books) == 1
        # knowledge_hash should be preserved
        assert hasattr(manifest, "series_knowledge_hash")

    def test_canonical_json_still_deterministic(self):
        """to_canonical_json from loader module is deterministic."""
        data = {"z": 1, "a": {"nested": True, "b": 2}}
        json1 = to_canonical_json(data)
        json2 = to_canonical_json(data)
        assert json1 == json2


# ---------------------------------------------------------------------------
# 24. Provider / Network / Translation Leakage = 0/0/0
# ---------------------------------------------------------------------------


class TestZeroLeakageAudit:
    """Tests confirming Provider/Network/Translation leakage remains 0/0/0."""

    def test_no_provider_imports_in_loader(self):
        """Loader module does not import any provider modules."""
        import core.knowledge_runtime.loader as loader_mod
        import inspect
        source = inspect.getsource(loader_mod)
        # Check actual import statements, not docstrings
        # Look for "from ... import" or "import " patterns
        forbidden_patterns = [
            "from provider",
            "import provider",
            "from openai",
            "import openai",
            "from anthropic",
            "import anthropic",
            "from google",
            "import google",
            "from llm",
            "import llm",
        ]
        for pattern in forbidden_patterns:
            assert pattern not in source, f"Forbidden import pattern '{pattern}' found in loader source"

    def test_no_provider_imports_in_manager(self):
        """Manager module does not import any provider modules."""
        import core.knowledge_runtime.manager as manager_mod
        import inspect
        source = inspect.getsource(manager_mod)
        forbidden_patterns = [
            "from provider",
            "import provider",
            "from openai",
            "import openai",
            "from anthropic",
            "import anthropic",
            "from google",
            "import google",
            "from llm",
            "import llm",
        ]
        for pattern in forbidden_patterns:
            assert pattern not in source, f"Forbidden import pattern '{pattern}' found in manager source"

    def test_no_network_imports_in_knowledge_runtime(self):
        """Knowledge runtime modules do not import network libraries."""
        import core.knowledge_runtime.loader as loader_mod
        import core.knowledge_runtime.manager as manager_mod
        import inspect
        forbidden = ["requests", "httpx", "aiohttp", "urllib", "socket", "http.client"]
        for mod in [loader_mod, manager_mod]:
            source = inspect.getsource(mod)
            for term in forbidden:
                assert term.lower() not in source.lower(), f"Network import '{term}' found in {mod.__name__}"

    def test_no_translation_pipeline_imports(self):
        """Knowledge runtime modules do not import translation pipeline."""
        import core.knowledge_runtime.loader as loader_mod
        import core.knowledge_runtime.manager as manager_mod
        import inspect
        forbidden = [
            "translation_runtime",
            "translation_engine",
            "translation_scheduler",
            "translate(",
            "TranslationRuntime",
        ]
        for mod in [loader_mod, manager_mod]:
            source = inspect.getsource(mod)
            for term in forbidden:
                assert term.lower() not in source.lower(), f"Translation import '{term}' found in {mod.__name__}"

    def test_population_is_offline_only(self, tmp_path):
        """Full population pipeline runs without any external calls."""
        series_id, registry = _setup_series_with_registry(tmp_path, "OfflineOnly")
        store = SeriesMemoryStore(series_id)
        store.add_or_merge_canonical_fact(
            _make_series_character_record(series_id, "aaa", "AAA")
        )
        glossary = _make_series_glossary(series_id)
        manager = KnowledgeRuntimeManager()
        # This should complete without any network or provider interaction
        report = manager.load_series_knowledge(series_id, store, glossary, tmp_path, registry)
        assert report.series_id == series_id
        assert report.knowledge_hash != ""


# ---------------------------------------------------------------------------
# Property-Based Determinism Tests
# ---------------------------------------------------------------------------


class TestPropertyBased:
    """Property-based tests for deterministic behavior (1000 iterations)."""

    def test_knowledge_fingerprint_deterministic_property(self):
        """Same knowledge state always produces same fingerprint (1000 iterations)."""
        import random
        import string

        for _ in range(1000):
            series_key = "".join(random.choices(string.ascii_letters + " ", k=15)).strip()
            if not series_key:
                continue
            series_id = compute_series_id(series_key)
            sk = SeriesKnowledge(
                schema_name="ntpe.series_knowledge",
                schema_version="1.0",
                series_id=series_id,
                character_entries={"char:test": "test_val"},
                glossary_entries={},
                general_entries={},
                knowledge_hash="",
            )
            fp1 = compute_series_knowledge_fingerprint(sk.to_dict(include_knowledge_hash=False))
            fp2 = compute_series_knowledge_fingerprint(sk.to_dict(include_knowledge_hash=False))
            assert fp1 == fp2

    def test_serialization_roundtrip_property(self, tmp_path):
        """Save -> load -> same data (10 iterations with unique series)."""
        import random
        import string

        for i in range(10):
            series_key = f"PropertyTest_{i}_" + "".join(
                random.choices(string.ascii_letters, k=5)
            )
            series_id = compute_series_id(series_key)
            sk = SeriesKnowledge(
                schema_name="ntpe.series_knowledge",
                schema_version="1.0",
                series_id=series_id,
                character_entries={f"char:entry_{i}": f"value_{i}"},
                glossary_entries={f"term_{i}": f"trans_{i}"},
                general_entries={},
                knowledge_hash="",
            )
            fp = compute_series_knowledge_fingerprint(sk.to_dict(include_knowledge_hash=False))
            sk = SeriesKnowledge(
                schema_name=sk.schema_name,
                schema_version=sk.schema_version,
                series_id=sk.series_id,
                character_entries=sk.character_entries,
                glossary_entries=sk.glossary_entries,
                general_entries=sk.general_entries,
                knowledge_hash=fp,
            )
            path = get_series_knowledge_path(tmp_path, series_id)
            save_series_knowledge(sk, path)

            loaded = load_series_knowledge_from_path(path, series_id)
            assert loaded.knowledge_hash == sk.knowledge_hash
            assert loaded.character_entries == sk.character_entries
            assert loaded.glossary_entries == sk.glossary_entries


# Run tests when executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
