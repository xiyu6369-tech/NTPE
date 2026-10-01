"""S3 EPUB Translation Runtime Adapter.

Bridges EpubTranslationChunk objects to the canonical translation runtime
and maps canonical runtime results back to EPUB contract result models.

This is an integration layer ONLY. It does NOT:
- Build prompts
- Call providers
- Implement retry/recovery
- Run quality gates
- Manage memory
- Re-chunk or re-extract

All translation semantics are delegated to the canonical runtime chain:
    RuntimeOrchestrator → TranslationEngine → ProviderManager → NvidiaClient
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable

from core.epub_translation.contract import (
    EpubTranslationInput,
    EpubTranslationChunk,
    EpubChunkResult,
    EpubChapterResult,
    EpubTranslationResult,
)
from core.translation_engine.translation_engine import TranslationEngine
from core.runtime_orchestrator.manager import RuntimeOrchestrator
from core.runtime_orchestrator.models import RuntimeExecutionResult
from core.translation_runtime.models import TranslationRequest
from core.character_memory_v2 import MemoryStore, load_or_create_character_memory, save_character_memory, get_memory_file_path, compute_book_identity
from core.context_scene_memory import ContextMemoryStore, load_or_create_context_memory, save_context_memory, get_context_memory_file_path
from core.translation_quality_v5.best_attempt import select_best_attempt
from core.translation_runtime.runtime_qa import RuntimeQAPolicy, analyze_runtime_quality


DEFAULT_MODEL = "meta/llama-3.2-90b-vision-instruct"
DEFAULT_CHUNK_SIZE = 2000
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_SECONDS = 10.0
DEFAULT_CHARACTER_MEMORY = "memory/character_memory_lts.json"


@dataclass(frozen=True)
class EpubTranslationOptions:
    """Configuration for EPUB translation runtime integration.

    Mirrors TxtTranslationOptions where applicable but adapted for
    pre-chunked EPUB input.
    """

    translation_input: EpubTranslationInput
    chunks: tuple[EpubTranslationChunk, ...]
    model: str = DEFAULT_MODEL
    project_name: str = "NTPE EPUB Translation"
    source_language: str = "ko"
    target_language: str = "zh-TW"
    resume: bool = True
    dry_run: bool = False
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_base_seconds: float = DEFAULT_RETRY_BASE_SECONDS
    glossary_path: Path | None = None
    character_memory_path: Path | None = None
    strict_lock_terms: bool = True
    qa_enabled: bool = True
    qa_fail_policy: str = "retry"
    min_length_ratio: float = 0.18
    max_korean_chars: int = 2
    max_repeated_lines: int = 2
    output_formatter_enabled: bool = True
    taiwan_traditional_normalization: bool = True
    quality_profile: str = "novel"
    previous_context_chars: int = 700
    simplified_chinese_policy: str = "normalize"
    progress_enabled: bool = True
    speed: str = "balanced"
    provider_attempts: int | None = None
    qa_attempts: int | None = None
    runtime_timeout: int | None = None
    user_api_timeout: int | None = None
    naturalness_retry_limit: int | None = None
    quality_v5_enabled: bool = True
    quality_v5_report_enabled: bool = True
    quality_integration_v72: bool = False
    quality_character_memory_v72: bool = False
    quality_context_scene_v72: bool = False
    quality_naturalness_v72: bool = False
    quality_integration_kill_switch_v72: bool = False
    quality_character_store_v72: object | None = None
    quality_context_scene_store_v72: object | None = None
    quality_active_character_ids_v72: tuple[str, ...] = ()
    quality_chapter_id_v72: str | None = None
    quality_scene_id_v72: str | None = None
    quality_sequence_index_v72: int | None = None
    quality_selection_time_v72: str = "9999-01-01T00:00:00Z"
    quality_prompt_budget_v72: Any | None = None
    quality_delivery_v83: bool = False
    quality_delivery_formats_v83: tuple[str, ...] = ("txt",)


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _save_json(path: Path, data: dict) -> None:
    import json
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_locked_dictionary(root: Path, options: EpubTranslationOptions) -> dict[str, str]:
    """Load locked dictionary (glossary + character memory overrides)."""
    locked: dict[str, str] = {}
    for path in (root / "character_override.json", root / "glossary_override.json"):
        if path.exists():
            import json
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
                locked.update(_extract_pairs(data))
            except Exception:
                pass
        locked.update(_load_glossary_text(path))

    if options.glossary_path:
        custom = options.glossary_path if options.glossary_path.is_absolute() else root / options.glossary_path
        locked.update(_load_glossary_text(custom))
        import json
        try:
            data = json.loads(custom.read_text(encoding="utf-8-sig"))
            locked.update(_extract_pairs(data))
        except Exception:
            pass

    memory_path = _resolve_character_memory_path(root, options)
    if memory_path and memory_path.exists():
        import json
        try:
            data = json.loads(memory_path.read_text(encoding="utf-8-sig"))
            locked.update(_extract_pairs(data))
        except Exception:
            pass
    return locked


def _load_glossary_text(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    pairs: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        delimiter = "=" if "=" in line else "->" if "->" in line else "→" if "→" in line else None
        if delimiter is None:
            continue
        src, target = line.split(delimiter, 1)
        src = src.strip().strip("- ").strip()
        target = target.strip()
        if src and target:
            pairs[src] = target
    return pairs


def _extract_pairs(data: Any) -> dict[str, str]:
    if not isinstance(data, dict):
        return {}
    pairs: dict[str, str] = {}
    for k, v in data.items():
        if isinstance(k, str) and isinstance(v, str) and k and v:
            pairs[k] = v
        elif isinstance(v, dict):
            pairs.update(_extract_pairs(v))
    return pairs


def _resolve_character_memory_path(root: Path, options: EpubTranslationOptions) -> Path:
    if options.character_memory_path:
        return options.character_memory_path if options.character_memory_path.is_absolute() else root / options.character_memory_path
    return root / DEFAULT_CHARACTER_MEMORY


def _apply_locked_dictionary(text: str, locked_dictionary: dict[str, str]) -> str:
    """Apply locked dictionary to translation output."""
    result = text or ""
    # Apply target aliases first
    for target in locked_dictionary.values():
        if not target:
            continue
        from lts.txt_translation_runtime import DEFAULT_LOCKED_TRANSLATION_ALIASES
        for alias in DEFAULT_LOCKED_TRANSLATION_ALIASES.get(target, set()):
            if alias and alias != target:
                result = result.replace(alias, target)
    # Then apply source->target
    for source, target in sorted(locked_dictionary.items(), key=lambda item: len(item[0]), reverse=True):
        if source and target:
            result = result.replace(source, target)
    return result


def _format_translation_output(text: str, options: EpubTranslationOptions) -> str:
    """Format translation output (Taiwan traditional normalization, punctuation)."""
    result = text or ""
    if options.taiwan_traditional_normalization:
        from lts.txt_translation_runtime import TAIWAN_TRADITIONAL_REPLACEMENTS
        for s, t in TAIWAN_TRADITIONAL_REPLACEMENTS.items():
            result = result.replace(s, t)
    if options.output_formatter_enabled:
        import re
        result = result.replace("...", "……")
        result = result.replace(",", "，")
        result = result.replace(":", "：")
        result = result.replace(";", "；")
        result = result.replace("?", "？")
        result = result.replace("!", "！")
        result = result.replace("(", "（").replace(")", "）")
        result = re.sub(r'[“"]([^“”"\n]{1,200})[”"]', r'「\1」', result)
        result = re.sub(r"[‘']([^‘’'\n]{1,200})[’']", r"『\1』", result)
    return result


def _emit_progress(message: str, options: EpubTranslationOptions) -> None:
    if options.progress_enabled:
        print(f"[NTPE EPUB PROGRESS] {message}", flush=True)


def translate_epub_translation_input(
    options: EpubTranslationOptions,
    root: str | Path | None = None,
    engine: Any | None = None,
) -> EpubTranslationResult:
    """Translate EPUB using canonical translation runtime.

    This is the main S3 entry point. It:
    1. Validates that chunks match the translation input
    2. Sets up canonical runtime components (orchestrator, engine, memory)
    3. Processes each chunk through RuntimeOrchestrator.execute()
    4. Maps canonical results to EpubChunkResult
    5. Assembles EpubChapterResult and EpubTranslationResult

    Args:
        options: EpubTranslationOptions containing translation_input and chunks
        root: Project root path (defaults to repository root)

    Returns:
        EpubTranslationResult with chapter_results in spine order
    """
    root_path = Path(root) if root else Path(__file__).resolve().parents[2]
    translation_input = options.translation_input
    chunks = options.chunks

    # Validate chunk ownership against input
    from core.epub_translation.contract.validation import validate_chunk_ownership
    validate_chunk_ownership(translation_input, chunks)

    # Setup output directory
    book_id = translation_input.metadata.identifier or "unknown"
    output_dir = root_path / "output" / "epub_translation" / book_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load locked dictionary
    locked_dictionary = _load_locked_dictionary(root_path, options)

    # Initialize canonical runtime components
    orchestrator = RuntimeOrchestrator()
    if engine is not None:
        orchestrator.set_engine(engine)
    else:
        engine = TranslationEngine(root=root_path)
        orchestrator.set_engine(engine)

    # Character Memory v2
    lts_memory_path = options.character_memory_path
    if lts_memory_path and not lts_memory_path.exists():
        lts_memory_path = None
    character_memory_store, cm_load_report = load_or_create_character_memory(
        output_dir=output_dir,
        input_path=translation_input.source_epub_path,
        project_name=options.project_name,
        lts_path=lts_memory_path,
    )

    # Context/Scene Memory (feature-gated)
    enable_cross_chunk_context = getattr(options, "quality_context_scene_v72", False)
    context_memory_store = None
    if enable_cross_chunk_context:
        context_memory_store, csm_load_report = load_or_create_context_memory(
            output_dir=output_dir,
            input_path=translation_input.source_epub_path,
            project_name=options.project_name,
        )
    else:
        context_memory_store = ContextMemoryStore()

    # Resume state
    resume_state_path = output_dir / f"{translation_input.source_epub_path.stem}_epub_resume_state.json"
    resume_state = _load_resume_state(resume_state_path)
    resume_state["input"] = str(translation_input.source_epub_path)
    resume_state["output_dir"] = str(output_dir)
    resume_state["chunk_total"] = len(chunks)
    resume_state["updated_at"] = _now_iso()

    # Live progress
    live_progress_path = output_dir / f"{translation_input.source_epub_path.stem}_epub_live_progress.json"

    # Start runtime session
    session = orchestrator.start_session(metadata={
        "input": str(translation_input.source_epub_path),
        "chunk_total": len(chunks),
        "profile": options.quality_profile,
        "model": options.model,
        "pipeline": "epub_runtime",
        "enable_cross_chunk_context": enable_cross_chunk_context,
    })
    session_id = session.session_id
    _emit_progress(f"epub runtime session created: {session_id}", options)

    # Chapter/chunk grouping for sequential processing
    chunks_by_chapter: dict[str, list[EpubTranslationChunk]] = {}
    for chunk in chunks:
        chunks_by_chapter.setdefault(chunk.chapter_id, []).append(chunk)

    # Sort chapters by chapter_order (spine order)
    chapter_order_map = {c.chapter_id: c.spine_position for c in translation_input.chapter_map}
    sorted_chapter_ids = sorted(chunks_by_chapter.keys(), key=lambda cid: chapter_order_map.get(cid, 0))

    # Process chunks sequentially in spine order, chunk_sequence order within chapter
    all_chunk_results: list[EpubChunkResult] = []
    chapter_results: list[EpubChapterResult] = []
    current_chapter_id = ""
    current_scene_id = "scene_1"
    prev_chunk_text = ""

    from core.context_scene_memory.scene_state import transition_scene, transition_chapter
    from core.context_scene_memory.context_selection import select_context_for_translation
    from core.context_scene_memory.models import BoundaryType, ContextEvidence, EvidenceType
    from core.intelligence.narrative_engine import NarrativeIntelligenceEngine
    from core.runtime_session import RunStatus

    narrative_engine = NarrativeIntelligenceEngine() if enable_cross_chunk_context else None
    active_character_ids = options.quality_active_character_ids_v72 if enable_cross_chunk_context else ()

    for chapter_idx, chapter_id in enumerate(sorted_chapter_ids):
        chapter_chunks = chunks_by_chapter[chapter_id]
        # Sort by chunk_sequence
        chapter_chunks.sort(key=lambda c: c.chunk_sequence)

        chapter_chunk_results: list[EpubChunkResult] = []

        for chunk_seq, chunk in enumerate(chapter_chunks):
            _emit_progress(f"processing chunk {chunk.chunk_id} ({chunk_seq + 1}/{len(chapter_chunks)} of {chapter_id})", options)

            # Compute chunk_key and source_hash early (needed for both dry-run and resume)
            chunk_key = f"{chunk.chapter_id}:{chunk.chunk_sequence:04d}"
            source_hash = hashlib.sha256(chunk.source_text.encode("utf-8")).hexdigest()[:16]

            # Dry-run check first (before resume) so dry-run tests aren't affected by resume state
            if options.dry_run:
                _emit_progress(f"chunk {chunk.chunk_id} dry-run", options)
                chunk_result = EpubChunkResult(
                    chunk_id=chunk.chunk_id,
                    status="dry_run",
                    translated_text="",
                    error=None,
                    attempt=0,
                    qa_report=MappingProxyType({}),
                    metadata=MappingProxyType({"dry_run": True, "source_hash": source_hash}),
                )
                chapter_chunk_results.append(chunk_result)
                all_chunk_results.append(chunk_result)
                resume_state["chunks"][chunk_key] = {"status": "dry_run", "source_hash": source_hash, "updated_at": _now_iso()}
                _save_json(resume_state_path, resume_state)
                continue

            # Resume check
            state_entry = resume_state["chunks"].get(chunk_key, {})
            reusable_state = (
                options.resume
                and state_entry.get("status") in {"success", "pass_with_warning"}
                and state_entry.get("source_hash") == source_hash
            )

            if reusable_state:
                _emit_progress(f"chunk {chunk.chunk_id} resume hit", options)
                # Create success result from resume
                chunk_result = EpubChunkResult(
                    chunk_id=chunk.chunk_id,
                    status="skipped",
                    translated_text="",
                    error=None,
                    attempt=0,
                    qa_report=MappingProxyType({}),
                    metadata=MappingProxyType({"resumed": True, "source_hash": source_hash}),
                )
                chapter_chunk_results.append(chunk_result)
                all_chunk_results.append(chunk_result)
                continue

            # Cross-chunk context handling (RM-8.2)
            context_state_metadata = None
            context_selection = None
            scene_state = None
            narrative_context = {}
            entity_injection_set = None

            if enable_cross_chunk_context and context_memory_store is not None:
                # Boundary detection
                from core.translation_runtime.boundary_detector import detect_boundary
                boundary = detect_boundary(prev_chunk_text, chunk.source_text)

                if boundary.type != BoundaryType.SAME_SCENE:
                    if boundary.type == BoundaryType.CHAPTER_TRANSITION:
                        transition_chapter(
                            store=context_memory_store,
                            from_scene_id=current_scene_id,
                            to_scene_id=boundary.scene_id or f"scene_{chapter_idx + 1}",
                            to_chapter_id=boundary.chapter_id or chapter_id,
                            evidence=ContextEvidence(
                                evidence_id=f"ev_{hashlib.md5(chunk.source_text.encode()).hexdigest()[:12]}",
                                evidence_type=EvidenceType.SOURCE_OBSERVATION,
                                source_case_id="translation_session",
                                source_segment_id=f"chunk_{len(chunk.source_text)}",
                                source_text_hash=hashlib.sha256(chunk.source_text.encode()).hexdigest()[:16],
                                translation_text_hash=None,
                                excerpt=chunk.source_text[:200] if chunk.source_text else "",
                                language="ko",
                                rule_id=None,
                                observed_at=_now_iso(),
                            ),
                        )
                        current_chapter_id = boundary.chapter_id or chapter_id
                    elif boundary.type == BoundaryType.SCENE_TRANSITION:
                        transition_scene(
                            store=context_memory_store,
                            from_scene_id=current_scene_id,
                            boundary=boundary.type,
                            to_scene_id=boundary.scene_id,
                            evidence=ContextEvidence(
                                evidence_id=f"ev_{hashlib.md5(chunk.source_text.encode()).hexdigest()[:12]}",
                                evidence_type=EvidenceType.SOURCE_OBSERVATION,
                                source_case_id="translation_session",
                                source_segment_id=f"chunk_{len(chunk.source_text)}",
                                source_text_hash=hashlib.sha256(chunk.source_text.encode()).hexdigest()[:16],
                                translation_text_hash=None,
                                excerpt=chunk.source_text[:200] if chunk.source_text else "",
                                language="ko",
                                rule_id=None,
                                observed_at=_now_iso(),
                            ),
                        )
                    current_scene_id = boundary.scene_id or current_scene_id

                # Context selection
                selection = select_context_for_translation(
                    context_store=context_memory_store,
                    chapter_id=current_chapter_id,
                    scene_id=current_scene_id,
                    sequence_index=chunk_seq,
                    character_ids=active_character_ids,
                    token_budget=512,
                    character_token_budget=256,
                )
                context_selection = selection

                # Scene state
                scene_state = context_memory_store.get_scene(current_scene_id)

                # Narrative state
                if narrative_engine:
                    prev_translation = ""
                    if chapter_chunk_results:
                        # Find last successful translation
                        for cr in reversed(chapter_chunk_results):
                            if cr.status == "success" and cr.translated_text:
                                prev_translation = cr.translated_text
                                break
                    narrative_engine.analyze_chunk(source=chunk.source_text, translation=prev_translation)
                    narrative_context = narrative_engine.get_context_for_prompt()

                context_state_metadata = {
                    "context_selection_fingerprint": selection.deterministic_fingerprint,
                    "scene_id": current_scene_id,
                    "scene_version": scene_state.scene_version if scene_state else 0,
                    "narrative": narrative_context,
                    "boundary": boundary.to_dict(),
                    "selected_context_ids": tuple(r.item_id for r in selection.selected_records),
                }

            # Character memory scope
            character_memory_scope = {
                "chapter_id": chapter_id,
                "scene_id": current_scene_id,
                "session_id": session_id,
            }

            # Context memory scope
            context_memory_scope = {
                "chapter_id": chapter_id,
                "scene_id": current_scene_id,
                "session_id": session_id,
                "active_character_ids": active_character_ids,
                "source_language": options.source_language,
                "token_budget": 512,
            }

            # Build metadata for orchestrator
            metadata = {
                "source": {
                    "chunk_text": chunk.source_text,
                    "char_count": len(chunk.source_text),
                },
                "model_profile": {
                    "model": options.model,
                    "temperature": 0.15,
                    "max_output_tokens": 4000,
                    "top_p": 0.85,
                },
                "profile": options.quality_profile,
                "system_prompt": "",  # Will be built by orchestrator
                "enable_cross_chunk_context": enable_cross_chunk_context,
                "context_state": context_state_metadata,
                "context_selection": context_selection,
                "scene_state": scene_state,
                "narrative_state": narrative_context if enable_cross_chunk_context else None,
                "entity_injection_set": entity_injection_set,
                "character_memory_store": character_memory_store,
                "character_memory_scope": character_memory_scope,
                "context_memory_store": context_memory_store,
                "context_memory_scope": context_memory_scope,
                "provider_attempts": options.provider_attempts,
                "retry_base_seconds": options.retry_base_seconds,
                "character_memory_hash": None,
                "character_memory_snapshot_version": None,
                "context_memory_hash": None,
                "context_memory_snapshot_version": None,
                # EPUB-specific metadata for result correlation
                "epub_chunk_id": chunk.chunk_id,
                "epub_chapter_id": chunk.chapter_id,
                "epub_chapter_order": chunk.chapter_order,
                "epub_chunk_sequence": chunk.chunk_sequence,
                "epub_source_href": chunk.source_href,
                "epub_fragment": chunk.fragment,
            }

            # Execute through canonical runtime
            execution_result: RuntimeExecutionResult | None = None
            try:
                execution_result = orchestrator.execute(
                    chunk_text=chunk.source_text,
                    session_id=session_id,
                    snapshot_id=f"{chunk.chapter_id}:{chunk.chunk_sequence:04d}",
                    current_chunk=chunk_seq + 1,
                    total_chunks=len(chapter_chunks),
                    metadata=metadata,
                )

                response = execution_result.response
                provider_result = response if isinstance(response, dict) else {"status": "failed", "error": str(response)}
            except Exception as e:
                # Convert exception to failed provider result
                provider_result = {"status": "failed", "error": f"Runtime execution exception: {e}"}

            # Map canonical result to EpubChunkResult
            chunk_result = _map_canonical_result_to_chunk_result(
                chunk=chunk,
                provider_result=provider_result,
                execution_result=execution_result,
                locked_dictionary=locked_dictionary,
                options=options,
            )

            chapter_chunk_results.append(chunk_result)
            all_chunk_results.append(chunk_result)

            # Update resume state
            resume_state["chunks"][chunk_key] = {
                "status": chunk_result.status,
                "source_hash": source_hash,
                "updated_at": _now_iso(),
            }
            _save_json(resume_state_path, resume_state)

            # Update prev_chunk_text for next iteration
            prev_chunk_text = chunk.source_text

            # Persist memory stores
            if character_memory_store is not None:
                save_character_memory(character_memory_store, get_memory_file_path(output_dir, compute_book_identity(translation_input.source_epub_path, options.project_name)))
            if enable_cross_chunk_context and context_memory_store is not None:
                save_context_memory(context_memory_store, get_context_memory_file_path(output_dir, compute_book_identity(translation_input.source_epub_path, options.project_name)))

        # Assemble chapter result
        chapter_result = _assemble_chapter_result(
            chapter_id=chapter_id,
            chapter_order=chapter_order_map.get(chapter_id, chapter_idx + 1),
            chunk_results=tuple(chapter_chunk_results),
        )
        chapter_results.append(chapter_result)

    # Complete session
    # Dry-run or all-resume paths may skip execute() calls entirely.
    # Canonical lifecycle requires CREATED → RUNNING before COMPLETED.
    from core.runtime_session import RunStatus as _RS
    _state = orchestrator.session_manager.get_state(session_id)
    if _state is not None and _state.status == _RS.CREATED:
        orchestrator.session_manager.update_runtime(session_id, status=_RS.RUNNING)
    orchestrator.complete(session_id, success=True)

    # Persist final memory stores
    if character_memory_store is not None:
        save_character_memory(character_memory_store, get_memory_file_path(output_dir, compute_book_identity(translation_input.source_epub_path, options.project_name)))
    if enable_cross_chunk_context and context_memory_store is not None:
        save_context_memory(context_memory_store, get_context_memory_file_path(output_dir, compute_book_identity(translation_input.source_epub_path, options.project_name)))

    # Assemble final translation result
    translation_result = _assemble_translation_result(
        chapter_results=tuple(chapter_results),
        session_id=session_id,
        resume_state_path=resume_state_path,
    )

    return translation_result


def _normalize_provider_status(status: str) -> str:
    """Map provider status to valid EpubChunkResult status."""
    valid_statuses = {"success", "failed", "skipped", "dry_run", "incomplete"}
    if status in valid_statuses:
        return status
    # Unknown status -> treat as failed
    return "failed"


def _map_canonical_result_to_chunk_result(
    chunk: EpubTranslationChunk,
    provider_result: dict,
    execution_result: RuntimeExecutionResult | None,
    locked_dictionary: dict[str, str],
    options: EpubTranslationOptions,
) -> EpubChunkResult:
    """Map canonical runtime result to EpubChunkResult."""
    raw_status = provider_result.get("status", "failed")
    status = _normalize_provider_status(raw_status)
    error = provider_result.get("error")
    attempt = provider_result.get("attempt", 1)
    qa_report = provider_result.get("qa")

    # Apply locked dictionary if translation succeeded
    translated_text = ""
    if status == "success":
        translated_text = provider_result.get("translation", "")
        if not translated_text:
            out_path = provider_result.get("output_path", "")
            if out_path and Path(out_path).exists():
                translated_text = Path(out_path).read_text(encoding="utf-8")

        if translated_text and options.strict_lock_terms:
            translated_text = _apply_locked_dictionary(translated_text, locked_dictionary)
        translated_text = _format_translation_output(translated_text, options)

    # Build metadata
    metadata = {
        "epub_chunk_id": chunk.chunk_id,
        "epub_chapter_id": chunk.chapter_id,
        "epub_chapter_order": chunk.chapter_order,
        "epub_chunk_sequence": chunk.chunk_sequence,
        "epub_source_href": chunk.source_href,
        "epub_fragment": chunk.fragment,
        "provider_model": provider_result.get("provider_model"),
        "provider_elapsed_seconds": provider_result.get("provider_elapsed_seconds"),
        "orchestrator_version": execution_result.metadata.get("orchestrator_version") if execution_result and execution_result.metadata else None,
        "session_id": execution_result.session.get("session_id") if execution_result and execution_result.session else None,
        "prompt_hash": execution_result.request.get("prompt_hash") if execution_result and execution_result.request else None,
    }

    return EpubChunkResult(
        chunk_id=chunk.chunk_id,
        status=status,
        translated_text=translated_text,
        error=error,
        attempt=attempt,
        qa_report=MappingProxyType(qa_report) if qa_report else MappingProxyType({}),
        metadata=MappingProxyType(metadata),
    )


def _assemble_chapter_result(
    chapter_id: str,
    chapter_order: int,
    chunk_results: tuple[EpubChunkResult, ...],
) -> EpubChapterResult:
    """Assemble EpubChapterResult from chunk results in chunk_sequence order."""
    # Verify chunk_sequence order
    sorted_chunks = sorted(chunk_results, key=lambda c: c.chunk_id.split(":chunk")[-1] if ":chunk" in c.chunk_id else "0")

    success_count = sum(1 for c in chunk_results if c.status == "success")
    failed_count = sum(1 for c in chunk_results if c.status == "failed")
    skipped_count = sum(1 for c in chunk_results if c.status == "skipped")
    incomplete_count = sum(1 for c in chunk_results if c.status == "incomplete")
    dry_run_count = sum(1 for c in chunk_results if c.status == "dry_run")

    # Determine aggregate status
    # Priority: failed > incomplete > skipped > dry_run > success
    if failed_count > 0:
        aggregate_status = "failed"
    elif incomplete_count > 0:
        aggregate_status = "incomplete"
    elif skipped_count > 0:
        aggregate_status = "incomplete"
    elif dry_run_count > 0:
        aggregate_status = "failed"
    elif success_count == len(chunk_results):
        aggregate_status = "success"
    else:
        aggregate_status = "incomplete"

    # Assemble translated text (only successful chunks, in order)
    assembled_parts = [c.translated_text for c in sorted_chunks if c.status == "success" and c.translated_text]
    assembled_text = "\n\n".join(assembled_parts).strip()
    if assembled_text:
        assembled_text += "\n"

    return EpubChapterResult(
        chapter_id=chapter_id,
        chapter_order=chapter_order,
        chunk_results=tuple(sorted_chunks),
        aggregate_status=aggregate_status,
        success_count=success_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        assembled_text=assembled_text,
    )


def _assemble_translation_result(
    chapter_results: tuple[EpubChapterResult, ...],
    session_id: str,
    resume_state_path: Path,
) -> EpubTranslationResult:
    """Assemble final EpubTranslationResult from chapter results."""
    # Verify chapter_order sequence
    sorted_chapters = sorted(chapter_results, key=lambda c: c.chapter_order)

    success_count = sum(cr.success_count for cr in chapter_results)
    failed_count = sum(cr.failed_count for cr in chapter_results)
    skipped_count = sum(cr.skipped_count for cr in chapter_results)

    # Determine aggregate status based on chapter aggregate statuses
    # Priority: failed > incomplete > success
    # But dry_run-only chapters (all chunks dry_run) should not count as "failed"
    chapter_statuses = set()
    for cr in chapter_results:
        # If chapter is "failed" but all chunks are dry_run, treat as "incomplete" for translation
        if cr.aggregate_status == "failed":
            chunk_statuses = {c.status for c in cr.chunk_results}
            if chunk_statuses == {"dry_run"}:
                chapter_statuses.add("incomplete")
            else:
                chapter_statuses.add("failed")
        else:
            chapter_statuses.add(cr.aggregate_status)

    # Priority: failed > incomplete > success
    if "failed" in chapter_statuses:
        aggregate_status = "failed"
    elif "incomplete" in chapter_statuses:
        aggregate_status = "incomplete"
    elif all(cr.aggregate_status == "success" for cr in chapter_results):
        aggregate_status = "success"
    else:
        aggregate_status = "incomplete"

    return EpubTranslationResult(
        aggregate_status=aggregate_status,
        chapter_results=tuple(sorted_chapters),
        success_count=success_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        session_id=session_id,
        resume_state_path=resume_state_path,
    )


def _load_resume_state(path: Path) -> dict:
    if not path.exists():
        return {"version": "1.0-epub-runtime", "chunks": {}, "events": []}
    try:
        import json
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {"version": "1.0-epub-runtime", "chunks": {}, "events": []}
    if not isinstance(data, dict):
        return {"version": "1.0-epub-runtime", "chunks": {}, "events": []}
    data.setdefault("version", "1.0-epub-runtime")
    data.setdefault("chunks", {})
    data.setdefault("events", [])
    return data