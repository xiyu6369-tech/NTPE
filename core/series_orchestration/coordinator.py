"""P0 Stage 5 Batch 5.7 — Series Translation Coordinator.

High-level orchestration for series translation workflows.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Optional

from .workflow import (
    SeriesCreateResult,
    BookAddResult,
    TranslationReport,
    PromotionReport,
    SeriesStatusReport,
    BookWorkflowState,
    SeriesWorkflowState,
    utc_now_iso,
)
from .validation import (
    validate_series_operation,
    validate_book_in_series,
    validate_workflow_transition,
    validate_series_lifecycle_transition,
    validate_promotion_approval_gate,
    validate_concurrent_books,
    validate_series_not_archived,
    validate_volume_number,
    validate_book_status_for_promotion,
)
from .runtime_integration import build_series_context, inject_series_context


class SeriesTranslationCoordinator:
    """High-level orchestration for series translation workflows."""

    version = "p0-stage5-batch5.7"

    def __init__(
        self,
        output_root: Path,
        series_registry: Any,  # SeriesRegistry from core.series_identity
        series_memory_store: Any,  # SeriesMemoryStore from core.series_memory
        series_entity_registry: Any,  # SeriesEntityRegistry from core.series_entity_registry
        series_glossary: Any,  # SeriesGlossary from core.glossary_builder
        series_knowledge: Any,  # SeriesKnowledge from core.knowledge_runtime.loader
        series_checkpoint_manager: Any,  # SeriesCheckpointManager from core.series_checkpoint
        translation_runtime: Any,  # TranslationRuntime from core.translation_runtime
    ):
        self.output_root = output_root
        self.series_registry = series_registry
        self.series_memory_store = series_memory_store
        self.series_entity_registry = series_entity_registry
        self.series_glossary = series_glossary
        self.series_knowledge = series_knowledge
        self.series_checkpoint_manager = series_checkpoint_manager
        self.translation_runtime = translation_runtime

        # Set series context on translation runtime for series-aware execution
        if hasattr(self.translation_runtime, "set_series_context"):
            self.translation_runtime.set_series_context(
                series_registry=series_registry,
                series_memory_store=series_memory_store,
                series_entity_registry=series_entity_registry,
                series_glossary=series_glossary,
                series_knowledge=series_knowledge,
                series_checkpoint_manager=series_checkpoint_manager,
            )

    def create_series(
        self,
        user_defined_series_key: str,
        series_name: str | None = None,
    ) -> SeriesCreateResult:
        """Create new series. Returns SeriesManifest."""
        # 1. Validate series_id doesn't exist
        canonical_key = user_defined_series_key.strip().lower()
        from core.series_identity.identity import compute_series_id
        series_id = compute_series_id(canonical_key)

        series_dir = self.output_root / "series" / series_id
        if series_dir.exists():
            raise ValueError(f"Series already exists: {series_id}")

        # 2. Create series via SeriesRegistry
        result = self.series_registry.create(user_defined_series_key, series_name)

        # 3. Create empty Series artifacts (they'll be created on first use)
        # SeriesMemoryStore, SeriesEntityRegistry, SeriesGlossary, SeriesKnowledge
        # are created lazily when needed

        return SeriesCreateResult(
            series_id=result.series_id,
            manifest=result.manifest,
            manifest_path=result.manifest_path,
        )

    def add_book(
        self,
        series_id: str,
        source_path: Path,
        title: str | None = None,
    ) -> BookAddResult:
        """Add book to series. Returns BookRef with volume_number."""
        # 1. Validate series_id exists
        series_manifest = self.series_registry.get(series_id)

        # 2. Validate series not archived
        validate_series_not_archived(series_manifest, "add_book")

        # 3. Validate no concurrent books in progress
        validate_concurrent_books(series_manifest, "add_book")

        # 4. Compute book_identity from source_path + series_name
        from core.character_memory_v2.persistence import compute_book_identity
        book_identity = compute_book_identity(source_path, series_manifest.series_name)

        # 5. Process book_intake to get BookIntakeResult and PreflightResult, then build Manifest
        from core.book_intake.intake_package import BookIntakeProcessor
        from core.book_intake.preflight import BookPreflightAnalyzer
        from core.book_intake.manifest import BookIntakeManifestBuilder

        intake_processor = BookIntakeProcessor()
        intake_result = intake_processor.process(source_path)

        preflight_analyzer = BookPreflightAnalyzer()
        preflight_result = preflight_analyzer.analyze(intake_result)

        manifest_builder = BookIntakeManifestBuilder()
        book_intake_manifest = manifest_builder.build(intake_result, preflight_result)

        # 6. Get content fingerprint
        content_fingerprint = hashlib.sha256(source_path.read_bytes()).hexdigest()

        # 7. Add book to SeriesRegistry (updates manifest, assigns volume_number)
        if title is None:
            title = source_path.stem

        book_add_result = self.series_registry.add_book(
            series_id=series_id,
            book_identity=book_identity,
            source_path=str(source_path),
            title=title,
            content_fingerprint=content_fingerprint,
            manifest_fingerprint=book_intake_manifest.manifest_fingerprint,
        )

        # 8. Create SeriesCheckpoint with new book reference (status="pending")
        self.series_checkpoint_manager.create_checkpoint(series_id, include_completed_books=True)

        return BookAddResult(
            volume_number=book_add_result.volume_number,
            book_identity=book_identity,
            book_entry=book_add_result.book_entry,
            manifest=book_add_result.manifest,
            manifest_path=book_add_result.manifest_path,
        )

    def translate_book(
        self,
        series_id: str,
        volume_number: int,
        *,
        dry_run: bool = False,
        options: Any | None = None,
    ) -> TranslationReport:
        """Translate a specific book in series with series context hydration."""
        # 1. Validate series_id, volume_number exist
        series_manifest = self.series_registry.get(series_id)
        book_entry = series_manifest.get_book(volume_number)
        if book_entry is None:
            raise ValueError(f"Book volume {volume_number} not found in series {series_id}")

        book_identity = book_entry.book_identity

        # 2. Validate book status can transition to in_progress
        validate_workflow_transition(book_entry.status.value, "in_progress", "translate_book")
        validate_series_not_archived(series_manifest, "translate_book")

        # 3. Set book status to "in_progress" in SeriesManifest
        updated_manifest = self.series_registry.set_book_status(series_id, volume_number, "in_progress")

        # 4. Build SeriesContext via runtime_integration
        series_context = build_series_context(
            series_id=series_id,
            book_identity=book_identity,
            output_root=self.output_root,
            series_registry=self.series_registry,
            series_memory_store=self.series_memory_store,
            series_entity_registry=self.series_entity_registry,
            series_glossary=self.series_glossary,
            series_knowledge=self.series_knowledge,
            series_checkpoint_manager=self.series_checkpoint_manager,
        )

        # 5. Inject series context into TranslationRuntime
        inject_series_context(
            runtime=self.translation_runtime,
            series_context=series_context,
            output_root=self.output_root,
            series_memory_store=self.series_memory_store,
            series_entity_registry=self.series_entity_registry,
            series_glossary=self.series_glossary,
            series_knowledge=self.series_knowledge,
            series_registry=self.series_registry,
            book_identity=book_identity,
        )

        # 6. Call translation_runtime.translate_txt() with series_id, book_identity
        # For dry-run, use TxtTranslationOptions with dry_run=True
        if dry_run:
            from lts.txt_translation_runtime import TxtTranslationOptions
            options = TxtTranslationOptions(
                input_path=Path(book_entry.source_path),
                output_dir=self.output_root / "translations" / book_identity,
                source_language="ko",
                target_language="zh",
                dry_run=True,
            )

        # Call translate with series context
        try:
            result = self.translation_runtime.translate_txt(
                options,
                series_id=series_id,
                book_identity=book_identity,
            )

            status = result.get("status", "failed")
            chunks_translated = result.get("chunks_translated", 0)
            total_chunks = result.get("total_chunks", 0)
            error = result.get("error")

            # 7. On completion: set book status to "completed"
            if status == "success":
                self.series_registry.set_book_status(series_id, volume_number, "completed")

            # 8. Create SeriesCheckpoint
            checkpoint_report = self.series_checkpoint_manager.create_checkpoint(series_id, include_completed_books=True)

            # 9. Return TranslationReport
            return TranslationReport(
                series_id=series_id,
                book_identity=book_identity,
                volume_number=volume_number,
                status=status,
                chunks_translated=chunks_translated,
                total_chunks=total_chunks,
                hydration_summary=None,  # TODO: get from inject_series_context
                checkpoint_id=checkpoint_report.checkpoint_id,
                error=error,
            )

        except Exception as e:
            # On failure, set book status to "failed"
            self.series_registry.set_book_status(series_id, volume_number, "failed")
            raise

    def promote_book(
        self,
        series_id: str,
        volume_number: int,
        *,
        approval_gate: bool = True,
    ) -> PromotionReport:
        """Promote completed book facts to series (MANUAL gate)."""
        # 1. Validate promotion approval gate (D-07 frozen)
        validate_promotion_approval_gate(approval_gate, "promote_book")

        # 2. Validate series_id, volume_number, book status = "completed"
        series_manifest = self.series_registry.get(series_id)
        book_entry = series_manifest.get_book(volume_number)
        if book_entry is None:
            raise ValueError(f"Book volume {volume_number} not found in series {series_id}")

        book_identity = book_entry.book_identity
        validate_book_status_for_promotion(book_entry.status.value, "promote_book")
        validate_series_not_archived(series_manifest, "promote_book")

        # 3. Load BookMemoryStore
        from core.character_memory_v2.persistence import load_or_create_character_memory
        book_memory_store, _ = load_or_create_character_memory(
            output_dir=self.output_root,
            input_path=Path(book_entry.source_path),
            project_name=series_manifest.series_name,
        )

        # 4. Get EntityResolver user_overrides from book translation
        # This would be available if translation was done with series context
        # For now, we'll attempt to get it from the runtime if available
        resolver_user_overrides = {}
        if hasattr(self.translation_runtime, "_last_entity_resolver_overrides"):
            resolver_user_overrides = self.translation_runtime._last_entity_resolver_overrides or {}

        # 5. Promote: SeriesMemoryStore.promote_from_book() (MANUAL gate)
        memory_promotion = self.series_memory_store.promote_from_book(
            book_store=book_memory_store,
            book_identity=book_identity,
            approval_gate=approval_gate,
        )

        # 6. Promote: SeriesEntityRegistry.promote_from_resolver() (MANUAL gate)
        entity_promotion = self.series_entity_registry.promote_from_resolver(
            resolver_user_overrides=resolver_user_overrides,
            book_identity=book_identity,
            approval_gate=approval_gate,
        )

        # 7. Promote: merge_into_series_glossary() (MANUAL gate)
        # Load book glossary from analysis file
        book_glossary = self._load_book_glossary(book_identity)
        updated_glossary, glossary_promotion = self._promote_glossary(
            series_id=series_id,
            book_glossary=book_glossary,
            book_identity=book_identity,
            approval_gate=approval_gate,
        )

        # 8. Repopulate KnowledgeRuntime Novel tier
        from core.knowledge_runtime.manager import KnowledgeRuntimeManager
        km = KnowledgeRuntimeManager()
        knowledge_report = km.load_series_knowledge(
            series_id=series_id,
            series_memory_store=self.series_memory_store,
            series_glossary=updated_glossary,
            output_root=self.output_root,
            series_registry=self.series_registry,
        )

        # 9. Update all manifest hashes
        self.series_registry.update_series_memory_hash(series_id, self.series_memory_store.series_memory_hash)
        self.series_registry.update_series_entity_registry_hash(series_id, self.series_entity_registry.get_registry_hash())
        self.series_registry.update_series_glossary_hash(series_id, updated_glossary.glossary_hash)
        self.series_registry.update_series_knowledge_hash(series_id, knowledge_report.knowledge_hash)

        # 10. Set book status to "promoted"
        self.series_registry.set_book_status(series_id, volume_number, "promoted")

        # 11. Create SeriesCheckpoint
        checkpoint_report = self.series_checkpoint_manager.create_checkpoint(series_id, include_completed_books=True)

        return PromotionReport(
            series_id=series_id,
            book_identity=book_identity,
            volume_number=volume_number,
            promotion_results=(),
            memory_promotion=memory_promotion,
            entity_promotion=entity_promotion,
            glossary_promotion=glossary_promotion,
            series_memory_hash=self.series_memory_store.series_memory_hash,
            series_entity_registry_hash=self.series_entity_registry.get_registry_hash(),
            series_glossary_hash=updated_glossary.glossary_hash,
            series_knowledge_hash=knowledge_report.knowledge_hash,
            series_checkpoint_hash=checkpoint_report.state_hash,
        )

    def _load_book_glossary(self, book_identity: str) -> dict:
        """Load book glossary from analysis file for promotion."""
        analysis_dir = self.output_root.parent / "analysis"
        if not analysis_dir.exists():
            return {}

        from core.glossary_builder import infer_book_name
        for file in analysis_dir.glob("*_glossary_auto.json"):
            if infer_book_name(file) == book_identity:
                from core.glossary_builder import load_json
                data = load_json(file)
                if isinstance(data, dict):
                    return data
        return {}

    def _promote_glossary(
        self,
        series_id: str,
        book_glossary: dict,
        book_identity: str,
        approval_gate: bool,
    ):
        """Promote glossary terms from book to series."""
        # Load current series glossary
        from core.glossary_builder import load_series_glossary, merge_into_series_glossary
        series_glossary = load_series_glossary(series_id, self.output_root)

        updated_glossary, promotion_records = merge_into_series_glossary(
            series_glossary=series_glossary,
            book_glossary=book_glossary,
            book_identity=book_identity,
            approval_gate=approval_gate,
        )

        # Save updated glossary
        from core.glossary_builder import save_series_glossary, get_series_glossary_path
        save_series_glossary(updated_glossary, get_series_glossary_path(self.output_root, series_id))

        return updated_glossary, promotion_records

    def get_series_status(self, series_id: str) -> SeriesStatusReport:
        """Get current series status: books, progress, next actions."""
        # 1. Load SeriesManifest
        series_manifest = self.series_registry.get(series_id)

        # 2. Load latest SeriesCheckpoint
        checkpoint = self.series_checkpoint_manager.load_latest_checkpoint(series_id)

        # 3. Build SeriesWorkflowState from manifest + checkpoint
        books = []
        next_actions = []

        for book_entry in series_manifest.books:
            # Get checkpoint info for this book
            book_ref = None
            if checkpoint:
                for ref in checkpoint.book_checkpoints:
                    if ref.book_identity == book_entry.book_identity:
                        book_ref = ref
                        break

            books.append(BookWorkflowState(
                volume_number=book_entry.volume_number,
                book_identity=book_entry.book_identity,
                status=book_entry.status.value,
                hydration_done=book_ref is not None and book_ref.book_memory_hash != "",
                translation_started_at=book_entry.completed_at if book_entry.status.value in ("completed", "promoted") else None,
                translation_completed_at=book_entry.completed_at if book_entry.status.value in ("completed", "promoted") else None,
                promotion_completed_at=book_entry.promoted_at if book_entry.status.value == "promoted" else None,
                current_chunk=0,  # TODO: get from session checkpoint
                total_chunks=0,  # TODO: get from book intake
                last_error=None,
            ))

            # Determine next actions
            if book_entry.status.value == "pending":
                next_actions.append(f"translate:volume_{book_entry.volume_number}")
            elif book_entry.status.value == "completed":
                next_actions.append(f"promote:volume_{book_entry.volume_number}")

        workflow_state = SeriesWorkflowState(
            series_id=series_id,
            series_name=series_manifest.series_name,
            lifecycle_status=series_manifest.lifecycle_status.value,
            books=tuple(books),
            next_volume_number=series_manifest.next_volume_number(),
            next_actions=next_actions,
        )

        return SeriesStatusReport(
            series_id=series_id,
            series_name=series_manifest.series_name,
            lifecycle_status=series_manifest.lifecycle_status.value,
            workflow_state=workflow_state,
            manifest=series_manifest,
            latest_checkpoint=checkpoint,
        )

    def resume_series(self, series_id: str):
        """Resume entire series from checkpoint."""
        from core.series_checkpoint.recovery import resume_series
        return resume_series(
            series_id=series_id,
            output_root=self.output_root,
            series_registry=self.series_registry,
            series_memory_store=self.series_memory_store,
            series_entity_registry=self.series_entity_registry,
            series_glossary=self.series_glossary,
            series_knowledge=self.series_knowledge,
        )

    def resume_book(self, series_id: str, volume_number: int):
        """Resume specific book in series."""
        from core.series_checkpoint.recovery import resume_book_in_series
        series_manifest = self.series_registry.get(series_id)
        book_entry = series_manifest.get_book(volume_number)
        if book_entry is None:
            raise ValueError(f"Book volume {volume_number} not found in series {series_id}")
        return resume_book_in_series(
            series_id=series_id,
            book_identity=book_entry.book_identity,
            output_root=self.output_root,
            series_registry=self.series_registry,
            series_memory_store=self.series_memory_store,
            series_entity_registry=self.series_entity_registry,
            series_glossary=self.series_glossary,
            series_knowledge=self.series_knowledge,
        )