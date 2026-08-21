"""P0 Stage 5 Batch 5.7 — Series Orchestration CLI Integration.

CLI command implementations for series management.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .coordinator import SeriesTranslationCoordinator
from .workflow import SeriesStatusReport


def _print_json(payload: object) -> None:
    """Print JSON with consistent formatting."""
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _series_to_dict(series: Any) -> dict:
    """Convert SeriesIdentity to dict."""
    return {
        "series_id": series.series_id,
        "series_name": series.series_name,
        "created_at": series.created_at,
        "updated_at": series.updated_at,
    }


def cmd_series_create(
    coordinator: SeriesTranslationCoordinator,
    series_name: str,
) -> None:
    """ntpe series create "Series Name" """
    user_key = series_name.strip()
    result = coordinator.create_series(user_key, series_name)
    _print_json({
        "status": "success",
        "series_id": result.series_id,
        "series_name": result.manifest.series_name,
        "manifest_path": str(result.manifest_path),
    })


def cmd_series_list(
    coordinator: SeriesTranslationCoordinator,
) -> None:
    """ntpe series list"""
    series_list = coordinator.series_registry.list_all()
    _print_json({
        "status": "success",
        "series": [_series_to_dict(s) for s in series_list],
    })


def cmd_series_status(
    coordinator: SeriesTranslationCoordinator,
    series_name: str,
) -> None:
    """ntpe series status "Series Name" """
    # Resolve series name to series_id
    series_list = coordinator.series_registry.list_all()
    series_match = None
    for s in series_list:
        if s.series_name == series_name:
            series_match = s
            break
    if series_match is None:
        # Try as series_id directly
        try:
            report = coordinator.get_series_status(series_name)
        except Exception:
            _print_json({"status": "error", "message": f"Series not found: {series_name}"})
            return
    else:
        report = coordinator.get_series_status(series_match.series_id)

    _print_json({
        "status": "success",
        "series_id": report.series_id,
        "series_name": report.series_name,
        "lifecycle_status": report.lifecycle_status,
        "workflow_state": report.workflow_state.to_dict(),
        "latest_checkpoint": report.latest_checkpoint.to_dict() if report.latest_checkpoint else None,
    })


def cmd_series_rename(
    coordinator: SeriesTranslationCoordinator,
    old_name: str,
    new_name: str,
) -> None:
    """ntpe series rename "Old Name" "New Name" """
    # Resolve series name to series_id
    series_list = coordinator.series_registry.list_all()
    series_match = None
    for s in series_list:
        if s.series_name == old_name:
            series_match = s
            break
    if series_match is None:
        _print_json({"status": "error", "message": f"Series not found: {old_name}"})
        return

    manifest = coordinator.series_registry.update_name(series_match.series_id, new_name)
    _print_json({
        "status": "success",
        "series_id": manifest.series_id,
        "series_name": manifest.series_name,
        "updated_at": manifest.updated_at,
    })


def cmd_series_add_book(
    coordinator: SeriesTranslationCoordinator,
    series_name: str,
    source_path: Path,
    title: str | None = None,
) -> None:
    """ntpe series add-book "Series Name" path/to/file.txt"""
    # Resolve series name to series_id
    series_list = coordinator.series_registry.list_all()
    series_match = None
    for s in series_list:
        if s.series_name == series_name:
            series_match = s
            break
    if series_match is None:
        _print_json({"status": "error", "message": f"Series not found: {series_name}"})
        return

    result = coordinator.add_book(series_match.series_id, source_path, title)
    _print_json({
        "status": "success",
        "series_id": series_match.series_id,
        "volume_number": result.volume_number,
        "book_identity": result.book_identity,
        "title": result.book_entry.title,
        "status": result.book_entry.status.value,
        "manifest_path": str(result.manifest_path),
    })


def cmd_series_promote_book(
    coordinator: SeriesTranslationCoordinator,
    series_name: str,
    volume_number: int,
) -> None:
    """ntpe series promote-book "Series Name" --book 1"""
    # Resolve series name to series_id
    series_list = coordinator.series_registry.list_all()
    series_match = None
    for s in series_list:
        if s.series_name == series_name:
            series_match = s
            break
    if series_match is None:
        _print_json({"status": "error", "message": f"Series not found: {series_name}"})
        return

    report = coordinator.promote_book(series_match.series_id, volume_number)
    _print_json({
        "status": "success",
        "series_id": report.series_id,
        "volume_number": report.volume_number,
        "book_identity": report.book_identity,
        "series_memory_hash": report.series_memory_hash,
        "series_entity_registry_hash": report.series_entity_registry_hash,
        "series_glossary_hash": report.series_glossary_hash,
        "series_knowledge_hash": report.series_knowledge_hash,
        "series_checkpoint_hash": report.series_checkpoint_hash,
    })


def cmd_translate_with_series(
    coordinator: SeriesTranslationCoordinator,
    series_name: str,
    volume_number: int,
    *,
    dry_run: bool = False,
) -> None:
    """ntpe translate --series "Series Name" --book 1"""
    # Resolve series name to series_id
    series_list = coordinator.series_registry.list_all()
    series_match = None
    for s in series_list:
        if s.series_name == series_name:
            series_match = s
            break
    if series_match is None:
        _print_json({"status": "error", "message": f"Series not found: {series_name}"})
        return

    report = coordinator.translate_book(series_match.series_id, volume_number, dry_run=dry_run)
    _print_json({
        "status": report.status,
        "series_id": report.series_id,
        "volume_number": report.volume_number,
        "book_identity": report.book_identity,
        "chunks_translated": report.chunks_translated,
        "total_chunks": report.total_chunks,
        "checkpoint_id": report.checkpoint_id,
        "error": report.error,
    })


def cmd_series_resume(
    coordinator: SeriesTranslationCoordinator,
    series_name: str,
    volume_number: int | None = None,
) -> None:
    """ntpe series resume "Series Name" [--book 2]"""
    # Resolve series name to series_id
    series_list = coordinator.series_registry.list_all()
    series_match = None
    for s in series_list:
        if s.series_name == series_name:
            series_match = s
            break
    if series_match is None:
        _print_json({"status": "error", "message": f"Series not found: {series_name}"})
        return

    if volume_number:
        report = coordinator.resume_book(series_match.series_id, volume_number)
        _print_json({
            "status": "success",
            "series_id": report.series_id,
            "book_identity": report.book_identity,
            "volume_number": report.volume_number,
            "book_memory_hash": report.book_memory_hash,
            "book_context_hash": report.book_context_hash,
            "session_checkpoint": report.session_checkpoint.to_dict() if report.session_checkpoint else None,
            "next_chunk_index": report.next_chunk_index,
        })
    else:
        report = coordinator.resume_series(series_match.series_id)
        _print_json({
            "status": "success",
            "series_id": report.series_id,
            "series_checkpoint_id": report.series_checkpoint_id,
            "series_manifest": report.series_manifest.to_dict() if hasattr(report.series_manifest, 'to_dict') else str(report.series_manifest),
            "books_to_resume": [
                {
                    "volume_number": b.volume_number,
                    "book_identity": b.book_identity,
                    "book_status": b.book_status,
                    "latest_session_id": b.latest_session_id,
                    "next_chunk_index": b.next_chunk_index,
                    "hydration_required": b.hydration_required,
                }
                for b in report.books_to_resume
            ],
            "next_actions": report.next_actions,
        })


__all__ = [
    "cmd_series_create",
    "cmd_series_list",
    "cmd_series_status",
    "cmd_series_rename",
    "cmd_series_add_book",
    "cmd_series_promote_book",
    "cmd_translate_with_series",
    "cmd_series_resume",
]