from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

from core.launcher_product.command_builder import build_translation_command
from core.launcher_product.languages import inspect_text_file
from core.launcher_product.models import CommandBuildResult, InputFileInspection, LauncherConfig, ValidationResult
from core.launcher_product.validation import validate_launcher_config


class LauncherController:
    def __init__(self, environment: Mapping[str, str] | None = None) -> None:
        self._environment = environment

    def inspect_input(self, path: str) -> InputFileInspection:
        return inspect_text_file(path)

    def validate(self, config: LauncherConfig) -> ValidationResult:
        return validate_launcher_config(config, environment=self._environment)

    def preview(self, config: LauncherConfig) -> CommandBuildResult:
        return build_translation_command(config, environment=self._environment)

    def _is_epub(self, config: LauncherConfig) -> bool:
        """Check if input file is EPUB format."""
        return Path(config.input_path).suffix.lower() == ".epub"

    def _build_txt_options(self, config: LauncherConfig, root_path: Path):
        """Build TXT translation options from launcher config."""
        from lts.txt_translation_runtime import TxtTranslationOptions

        return TxtTranslationOptions(
            input_path=Path(config.input_path),
            output_dir=Path(config.output_directory),
            chunk_size=config.chunk_size,
            model=config.model_id,
            project_name="NTPE Novel Translation",
            source_language=config.source_language,
            target_language=config.target_language,
            resume=config.resume_enabled,
            dry_run=config.dry_run,
            max_retries=3,
            retry_base_seconds=5.0,
            glossary_path=None,
            character_memory_path=None,
            strict_lock_terms=True,
            qa_enabled=True,
            qa_fail_policy="retry",
            min_length_ratio=0.18,
            max_korean_chars=2,
            max_repeated_lines=2,
            output_formatter_enabled=True,
            taiwan_traditional_normalization=True,
            quality_profile=config.translation_profile,
            previous_context_chars=700,
            simplified_chinese_policy="normalize",
            progress_enabled=True,
            speed="balanced",
            quality_v5_enabled=True,
            quality_v5_report_enabled=True,
            quality_integration_v72=False,
            quality_character_memory_v72=False,
            quality_context_scene_v72=False,
            quality_naturalness_v72=False,
            quality_integration_kill_switch_v72=False,
            quality_delivery_v83=False,
            quality_delivery_formats_v83=("txt",),
        )

    def _build_epub_options(self, config: LauncherConfig, root_path: Path):
        """Build EPUB translation options from launcher config.
        
        This performs the full EPUB extraction, intake, and chunking pipeline
        to prepare EpubTranslationOptions for the canonical EPUB runtime.
        """
        from core.adapters.epub_extraction_boundary import EpubExtractionBoundary
        from core.adapters.canonical_book_intake_adapter import CanonicalBookIntakeAdapter
        from core.adapters.epub_extraction_boundary import ExtractedTextIntakeRequest
        from core.epub_translation.chunking import chunk_epub_translation_input, ChunkingOptions
        from core.epub_translation.contract import (
            EpubTranslationInput, EpubMetadata, EpubChapterBoundary,
            ResourceRef, TocEntry, ExtractionManifest
        )
        from core.epub_translation.runtime.adapter import EpubTranslationOptions
        from types import MappingProxyType

        epub_path = Path(config.input_path)
        output_dir = Path(config.output_directory)

        # Step 1: Extract EPUB
        extractor = EpubExtractionBoundary()
        extraction_result = extractor.extract(epub_path)

        # Step 2: Create intake request
        intake_request = ExtractedTextIntakeRequest(
            source_path=extraction_result.source_path,
            source_format="epub",
            extracted_text=extraction_result.extracted_text,
            original_file_hash=extraction_result.original_hash,
            extracted_text_hash=extraction_result.extracted_hash,
            epub_metadata=dict(extraction_result.metadata.raw) if extraction_result.metadata.raw else {},
            chapter_map=extraction_result.chapter_map,
            extraction_manifest=extraction_result.extraction_manifest,
            extractor_version=extraction_result.extraction_manifest.extractor_version,
            status=extraction_result.status,
            warnings=extraction_result.warnings,
        )

        # Step 3: Process through canonical intake adapter
        adapter = CanonicalBookIntakeAdapter()
        intake_result = adapter.ingest_extracted(intake_request)

        if not intake_result.submission_eligible:
            raise ValueError(f"EPUB intake not eligible for translation: {intake_result.status}")

        # Step 4: Build EpubTranslationInput from intake result
        # Convert extraction boundary types to contract types
        epub_metadata = EpubMetadata(
            title=intake_result.epub_metadata.get("title") if intake_result.epub_metadata else None,
            author=intake_result.epub_metadata.get("author") if intake_result.epub_metadata else None,
            language=intake_result.epub_metadata.get("language") if intake_result.epub_metadata else None,
            identifier=intake_result.epub_metadata.get("identifier") if intake_result.epub_metadata else None,
            publisher=intake_result.epub_metadata.get("publisher") if intake_result.epub_metadata else None,
            date=intake_result.epub_metadata.get("date") if intake_result.epub_metadata else None,
            raw=MappingProxyType(dict(intake_result.epub_metadata.get("raw", {})) if intake_result.epub_metadata else {}),
        )

        chapter_map = tuple(
            EpubChapterBoundary(
                index=cb.index,
                spine_position=cb.spine_position,
                title=cb.title,
                source_href=cb.source_href,
                start_offset=cb.start_offset,
                end_offset=cb.end_offset,
                is_linear=cb.is_linear,
                word_count=cb.word_count,
                body_start_offset=cb.body_start_offset,
                body_end_offset=cb.body_end_offset,
                landmark_type=cb.landmark_type,
                status=cb.status,
                toc_level=cb.toc_level,
            )
            for cb in (intake_result.chapter_map or ())
        )

        resources = tuple(
            ResourceRef(
                type=rr.type,
                href=rr.href,
                chapter_index=rr.chapter_index,
                metadata=MappingProxyType(dict(rr.metadata)),
            )
            for rr in (intake_result.resource_refs or ())
        )

        extraction_manifest = None
        if intake_result.extraction_manifest:
            extraction_manifest = ExtractionManifest(
                extractor_version=intake_result.extraction_manifest.extractor_version,
                extracted_at=intake_result.extraction_manifest.extracted_at,
                chapter_count=intake_result.extraction_manifest.chapter_count,
                total_characters=intake_result.extraction_manifest.total_characters,
                total_words=intake_result.extraction_manifest.total_words,
                warnings=intake_result.extraction_manifest.warnings,
                resources=resources,
                spine_item_count=intake_result.extraction_manifest.spine_item_count,
                nav_toc_entries=intake_result.extraction_manifest.nav_toc_entries,
                encoding_used=intake_result.extraction_manifest.encoding_used,
                parsing_duration_ms=intake_result.extraction_manifest.parsing_duration_ms,
                fixed_layout=intake_result.extraction_manifest.fixed_layout,
            )

        translation_input = EpubTranslationInput(
            source_epub_path=epub_path,
            original_hash=extraction_result.original_hash,
            extraction_status=extraction_result.status,
            warnings=extraction_result.warnings,
            metadata=epub_metadata,
            chapter_map=chapter_map,
            resources=resources,
            toc_entries=(),
            fixed_layout_info=intake_result.extraction_manifest.fixed_layout if intake_result.extraction_manifest else None,
            extraction_manifest=extraction_manifest,
        )

        # Step 5: Chunk the translation input
        chunking_options = ChunkingOptions(chunk_size=config.chunk_size)
        chunks = chunk_epub_translation_input(translation_input, extraction_result.extracted_text, chunking_options)

        # Step 6: Build EPUB translation options
        return EpubTranslationOptions(
            translation_input=translation_input,
            chunks=chunks,
            model=config.model_id,
            project_name="NTPE EPUB Translation",
            source_language=config.source_language,
            target_language=config.target_language,
            resume=config.resume_enabled,
            dry_run=config.dry_run,
            max_retries=3,
            retry_base_seconds=10.0,
            glossary_path=None,
            character_memory_path=None,
            strict_lock_terms=True,
            qa_enabled=True,
            qa_fail_policy="retry",
            min_length_ratio=0.18,
            max_korean_chars=2,
            max_repeated_lines=2,
            output_formatter_enabled=True,
            taiwan_traditional_normalization=True,
            quality_profile=config.translation_profile,
            previous_context_chars=700,
            simplified_chinese_policy="normalize",
            progress_enabled=True,
            speed="balanced",
        )

    def start_translation(
        self,
        config: LauncherConfig,
        root_path: Path,
        on_progress: Callable[[dict], None],
        on_finished: Callable[[dict], None],
        on_error: Callable[[str], None],
    ) -> Any:
        """Start translation using canonical TranslationRuntime in background thread.

        Args:
            config: Launcher configuration
            root_path: Project root path
            on_progress: Progress callback
            on_finished: Completion callback
            on_error: Error callback

        Returns:
            TranslationRunner instance for lifecycle management
        """
        from ui.translation_launcher.worker import TranslationRunner

        if self._is_epub(config):
            options = self._build_epub_options(config, root_path)
        else:
            options = self._build_txt_options(config, root_path)

        runner = TranslationRunner(options, root_path)
        runner.start(on_progress, on_finished, on_error)
        return runner
