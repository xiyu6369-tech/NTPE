"""P0 Stage 5 Batch 5.7 — Series Orchestration Runtime Integration.

Series context injection into TranslationRuntime.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from core.runtime_checkpoint.models import ProgressState, RequestManifest


@dataclass(frozen=True)
class SeriesContext:
    """Series context injected into TranslationRuntime."""
    series_id: str
    book_identity: str
    volume_number: int
    series_memory_hash: str
    series_entity_registry_hash: str
    series_glossary_hash: str
    series_knowledge_hash: str
    book_memory_hash: str
    book_context_hash: str
    session_checkpoint_id: str | None
    series_manifest: Any

    def to_dict(self) -> dict:
        return {
            "series_id": self.series_id,
            "book_identity": self.book_identity,
            "volume_number": self.volume_number,
            "series_memory_hash": self.series_memory_hash,
            "series_entity_registry_hash": self.series_entity_registry_hash,
            "series_glossary_hash": self.series_glossary_hash,
            "series_knowledge_hash": self.series_knowledge_hash,
            "book_memory_hash": self.book_memory_hash,
            "book_context_hash": self.book_context_hash,
            "session_checkpoint_id": self.session_checkpoint_id,
        }


def build_series_context(
    series_id: str,
    book_identity: str,
    output_root: Path,
    series_registry: Any,
    series_memory_store: Any,
    series_entity_registry: Any,
    series_glossary: Any,
    series_knowledge: Any,
    series_checkpoint_manager: Any,
) -> SeriesContext:
    """
    Build series context for translation runtime.

    1. Load SeriesManifest → get book volume_number, source_path
    2. Load SeriesCheckpoint → get BookCheckpointRef for this book
    3. Validate all hashes (fail-closed)
    4. Get book memory hash, book context hash from checkpoint
    5. Get session checkpoint ID from checkpoint
    6. Return SeriesContext
    """
    # 1. Load SeriesManifest
    series_manifest = series_registry.get(series_id)

    # 2. Find book entry in manifest
    book_entry = series_manifest.get_book_by_identity(book_identity)
    if book_entry is None:
        raise ValueError(f"Book {book_identity} not found in series {series_id}")

    volume_number = book_entry.volume_number

    # 3. Load latest SeriesCheckpoint
    checkpoint = series_checkpoint_manager.load_latest_checkpoint(series_id)

    # 4. Get book checkpoint reference
    book_memory_hash = ""
    book_context_hash = ""
    session_checkpoint_id = None

    if checkpoint:
        for book_ref in checkpoint.book_checkpoints:
            if book_ref.book_identity == book_identity:
                book_memory_hash = book_ref.book_memory_hash
                book_context_hash = book_ref.book_context_hash
                session_checkpoint_id = book_ref.latest_session_checkpoint_id
                break

    # 5. Get Series artifact hashes
    series_memory_hash = getattr(series_memory_store, "series_memory_hash", "")
    series_entity_registry_hash = getattr(series_entity_registry, "get_registry_hash", lambda: "")()
    series_glossary_hash = getattr(series_glossary, "glossary_hash", "")
    series_knowledge_hash = getattr(series_knowledge, "knowledge_hash", "")

    return SeriesContext(
        series_id=series_id,
        book_identity=book_identity,
        volume_number=volume_number,
        series_memory_hash=series_memory_hash,
        series_entity_registry_hash=series_entity_registry_hash,
        series_glossary_hash=series_glossary_hash,
        series_knowledge_hash=series_knowledge_hash,
        book_memory_hash=book_memory_hash,
        book_context_hash=book_context_hash,
        session_checkpoint_id=session_checkpoint_id,
        series_manifest=series_manifest,
    )


def inject_series_context(
    runtime: Any,
    series_context: SeriesContext,
    output_root: Path,
    series_memory_store: Any,
    series_entity_registry: Any,
    series_glossary: Any,
    series_knowledge: Any,
    series_registry: Any,
    book_identity: str,
) -> None:
    """
    Inject series context into TranslationRuntime.

    1. Hydrate BookMemoryStore from SeriesMemoryStore
    2. Load BookContextStore (book-local)
    3. Get EntityResolver user_overrides from SeriesEntityRegistry.hydrate_resolver()
    4. Populate KnowledgeMerger Novel tier from SeriesKnowledge
    5. Populate KnowledgeMerger Volume tier from BookMemoryStore + BookGlossary
    6. Set GlossaryBuilder locked_dictionary from SeriesGlossary.get_locked_dictionary()
    7. Store series_context in runtime for use during translation
    """
    # 1. Hydrate BookMemoryStore from SeriesMemoryStore
    from core.character_memory_v2.persistence import load_or_create_character_memory
    from core.series_memory.hydration import hydrate_book_store

    book_memory_store, _ = load_or_create_character_memory(
        output_dir=output_root,
        input_path=Path(series_context.series_manifest.get_book_by_identity(book_identity).source_path),
        project_name=series_context.series_manifest.series_name,
    )

    hydration_summary = hydrate_book_store(
        series_store=series_memory_store,
        book_store=book_memory_store,
        book_identity=book_identity,
        series_memory_hash=series_context.series_memory_hash,
    )

    # 2. Load BookContextStore (book-local)
    from core.context_scene_memory.persistence import load_or_create_context_memory

    book_context_store, _ = load_or_create_context_memory(
        output_dir=output_root,
        input_path=Path(series_context.series_manifest.get_book_by_identity(book_identity).source_path),
        project_name=series_context.series_manifest.series_name,
    )

    # 3. Get EntityResolver user_overrides from SeriesEntityRegistry
    user_overrides, entity_hydration_report = series_entity_registry.hydrate_resolver(book_identity)

    # 4. Populate KnowledgeMerger Novel tier from SeriesKnowledge
    from core.knowledge_runtime.manager import KnowledgeRuntimeManager

    km = KnowledgeRuntimeManager()
    km.load_series_knowledge(
        series_id=series_context.series_id,
        series_memory_store=series_memory_store,
        series_glossary=series_glossary,
        output_root=output_root,
        series_registry=series_registry,
    )

    # 5. Populate KnowledgeMerger Volume tier from BookMemoryStore + BookGlossary
    # Load book glossary
    book_glossary = _load_book_glossary(output_root, book_identity)
    km.populate_volume_tier(
        book_memory_store=book_memory_store,
        book_glossary=book_glossary,
        book_identity=book_identity,
    )

    # 6. Set GlossaryBuilder locked_dictionary from SeriesGlossary
    locked_dictionary = series_glossary.get_locked_dictionary()
    alias_map = series_glossary.get_alias_map()

    # 7. Store series context and hydrated stores in runtime
    runtime._series_context = series_context
    runtime._series_book_memory_store = book_memory_store
    runtime._series_book_context_store = book_context_store
    runtime._series_user_overrides = user_overrides
    runtime._series_locked_dictionary = locked_dictionary
    runtime._series_alias_map = alias_map
    runtime._series_hydration_summary = hydration_summary
    runtime._series_entity_hydration_report = entity_hydration_report

    # Store EntityResolver overrides for later promotion
    runtime._last_entity_resolver_overrides = user_overrides


def _load_book_glossary(output_root: Path, book_identity: str) -> dict:
    """Load book glossary from analysis file."""
    analysis_dir = output_root.parent / "analysis"
    if not analysis_dir.exists():
        return {}

    from core.glossary_builder import infer_book_name, load_json

    for file in analysis_dir.glob("*_glossary_auto.json"):
        if infer_book_name(file) == book_identity:
            data = load_json(file)
            if isinstance(data, dict):
                return data
    return {}


__all__ = [
    "SeriesContext",
    "build_series_context",
    "inject_series_context",
]