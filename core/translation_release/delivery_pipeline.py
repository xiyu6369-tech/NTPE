from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.translation_release.models import DeliveryManifest, QualityCertificate, DeliveryResult, TOCEntry
from core.translation_release.polish import polish_full_novel
from core.translation_release.validator import validate_final_novel, ValidationResult, ValidationCheck
from core.translation_release.metadata import (
    build_toc_from_chunk_records,
    inject_metadata_into_text,
    generate_delivery_manifest,
    generate_quality_certificate,
)
from core.translation_release.package import write_txt_delivery, write_json_delivery
from lts.txt_translation_runtime import TxtTranslationOptions


def _compute_matched_locked_terms(
    chunk_records: list[dict],
    locked_dictionary: dict[str, str],
) -> dict[str, str]:
    """
    Compute locked terms that were actually matched in source chunks.
    Uses existing runtime logic: collect from chunk source metadata or prompt packages.
    """
    matched: dict[str, str] = {}
    for rec in chunk_records:
        src = rec.get("source") or rec.get("metadata", {}).get("source")
        if isinstance(src, dict):
            chunk_text = src.get("chunk_text", "")
            for k, v in locked_dictionary.items():
                if k and k in chunk_text and v:
                    matched[k] = v
    return matched


def _aggregate_literary_quality(chunk_records: list[dict]) -> dict:
    """Aggregate literary_quality_* metrics from all chunk records."""
    hits = errors = warnings = 0
    passed = True
    issue_codes: list[str] = []
    for rec in chunk_records:
        qa = rec.get("qa") if isinstance(rec.get("qa"), dict) else {}
        metrics = qa.get("metrics") if isinstance(qa.get("metrics"), dict) else {}
        if metrics:
            hits += int(metrics.get("literary_quality_hits", 0))
            errors += int(metrics.get("literary_quality_errors", 0))
            warnings += int(metrics.get("literary_quality_warnings", 0))
            if not metrics.get("literary_quality_passed", True):
                passed = False
            issue_codes.extend(metrics.get("literary_quality_issue_codes", []))
    return {
        "hits": hits,
        "errors": errors,
        "warnings": warnings,
        "passed": passed,
        "issue_codes": list(dict.fromkeys(issue_codes)),
    }


def _aggregate_context_continuity(chunk_records: list[dict]) -> dict:
    """Aggregate scene/chapter info from RM-8.2 context_state_metadata."""
    scenes: set[str] = set()
    chapters: set[str] = set()
    scene_transitions = 0
    prev_scene: str | None = None
    for rec in chunk_records:
        ctx = rec.get("metadata", {}).get("context_state")
        if ctx:
            scene_id = ctx.get("scene_id")
            chapter_id = ctx.get("chapter_id")
            if scene_id:
                scenes.add(scene_id)
            if chapter_id:
                chapters.add(chapter_id)
            if prev_scene and scene_id != prev_scene:
                scene_transitions += 1
            prev_scene = scene_id
    return {
        "scene_count": len(scenes),
        "chapter_count": len(chapters),
        "scene_transitions": scene_transitions,
    }


def run_delivery_pipeline(
    *,
    assembled_text: str,
    translated_chunks: list[str],
    chunk_records: list[dict],
    locked_dictionary: dict[str, str],
    options: TxtTranslationOptions,
    input_path: Path,
    output_dir: Path,
) -> DeliveryResult:
    """
    Main delivery pipeline — called from txt_translation_runtime.py after final assembly.

    Feature-gated by: options.quality_delivery_v83
    Input: assembled_text (already finalized by existing pipeline), NOT re-assembled here.
    """
    novel_id = input_path.stem

    # 1. FINAL CANONICALIZATION (reuse existing) — on already-assembled text
    try:
        from core.translation_naturalness import canonicalize_novel_chinese, apply_literary_collocation_guard
        assembled_text = canonicalize_novel_chinese(assembled_text).text
        assembled_text = apply_literary_collocation_guard(assembled_text).text
    except ImportError:
        pass  # graceful if not available

    # 2. POLISH (NEW — full novel scope)
    polished_text, polish_metrics = polish_full_novel(
        assembled_text,
        taiwan_traditional_normalization=options.taiwan_traditional_normalization,
        enabled=options.output_formatter_enabled,
    )

    # 3. VALIDATION GATE (NEW)
    literary_quality_aggregate = _aggregate_literary_quality(chunk_records)
    context_continuity_aggregate = _aggregate_context_continuity(chunk_records)

    # Compute matched locked terms from runtime
    matched_terms = _compute_matched_locked_terms(chunk_records, locked_dictionary)

    qc_result = validate_final_novel(
        text=polished_text,
        locked_dictionary=locked_dictionary,
        chunk_records=chunk_records,
        literary_quality_aggregate=literary_quality_aggregate,
        options=options,
        matched_terms=matched_terms,
    )

    if not qc_result.overall_passed:
        return DeliveryResult(
            status="failed",
            output_path="",
            manifest_path="",
            qc_certificate_path="",
            error=f"Quality gate FAILED: score={qc_result.overall_score:.1f}, critical_failures={qc_result.failed_critical}",
        )

    # 4. METADATA & TOC (NEW — consumes RM-8.2 metadata)
    toc = build_toc_from_chunk_records(chunk_records, translated_chunks)
    quality_summary = f"PASS (score={qc_result.overall_score:.1f})"

    final_text = inject_metadata_into_text(
        polished_text,
        title=novel_id,
        date=getattr(options, "completed_at", "") or "",
        model=options.model,
        pipeline_version="NTPE_RM83_v1",
        toc=toc,
        quality_cert_summary=quality_summary,
    )

    # 5. GENERATE ARTIFACTS
    delivery_manifest = generate_delivery_manifest(
        novel_id=novel_id,
        input_path=str(input_path),
        output_path="",  # filled after write
        chunk_records=chunk_records,
        translated_chunks=translated_chunks,
        locked_dictionary=locked_dictionary,
        options=options,
        literary_quality_aggregate=literary_quality_aggregate,
        qc_result=qc_result,
        toc=toc,
        artifact_paths={},  # filled after write
    )

    quality_certificate = generate_quality_certificate(
        novel_id=novel_id,
        qc_result=qc_result,
        literary_quality_aggregate=literary_quality_aggregate,
        context_continuity_aggregate=context_continuity_aggregate,
    )

    # 6. WRITE PACKAGE + EXPORTERS (collect all paths BEFORE constructing DeliveryResult)
    formats = getattr(options, "quality_delivery_formats_v83", ("txt",))

    # Write core artifacts
    txt_path = write_txt_delivery(final_text, output_dir, novel_id)
    manifest_path = write_json_delivery(delivery_manifest, output_dir, novel_id, "delivery_manifest")
    qc_path = write_json_delivery(quality_certificate, output_dir, novel_id, "quality_certificate")

    epub_path: str | None = None
    pdf_path: str | None = None

    # Optional exporters (non-blocking, graceful fallback)
    if "epub" in formats:
        try:
            from core.translation_release.exporters.epub_exporter import EpubExporter
            exporter = EpubExporter()
            epub_candidate = output_dir / f"{novel_id}.epub"
            if exporter.export(polished_text=final_text, manifest=delivery_manifest, toc=toc, output_path=epub_candidate):
                epub_path = str(epub_candidate)
        except (ImportError, AttributeError):
            pass  # graceful: format unavailable

    if "pdf" in formats:
        try:
            from core.translation_release.exporters.pdf_exporter import PdfExporter
            exporter = PdfExporter()
            pdf_candidate = output_dir / f"{novel_id}.pdf"
            if exporter.export(polished_text=final_text, manifest=delivery_manifest, toc=toc, output_path=pdf_candidate):
                pdf_path = str(pdf_candidate)
        except (ImportError, AttributeError):
            pass  # graceful: format unavailable

    # 7. CONSTRUCT IMMUTABLE DeliveryResult ONCE with all paths
    return DeliveryResult(
        status="success",
        output_path=txt_path,
        manifest_path=manifest_path,
        qc_certificate_path=qc_path,
        epub_path=epub_path,
        pdf_path=pdf_path,
        error=None,
    )