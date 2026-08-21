from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.launcher_product.config import LauncherConfigError, load_launcher_config
from core.launcher_product.dry_run import build_dry_run
from core.launcher_product.languages import source_languages, target_languages
from core.launcher_product.model_catalog import model_catalog
from core.launcher_product.provider_catalog import provider_catalog
from core.launcher_product.validation import validate_launcher_config
from core.series_orchestration import (
    SeriesTranslationCoordinator,
    cmd_series_create,
    cmd_series_list,
    cmd_series_status,
    cmd_series_rename,
    cmd_series_add_book,
    cmd_series_promote_book,
    cmd_translate_with_series,
    cmd_series_resume,
)
from core.translation_runtime.runtime import TranslationRuntime
from core.series_identity.registry import SeriesRegistry
from core.series_memory.store import SeriesMemoryStore
from core.series_entity_registry.registry import SeriesEntityRegistry
from core.glossary_builder import load_series_glossary
from core.knowledge_runtime.loader import load_series_knowledge
from core.series_checkpoint.manager import SeriesCheckpointManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ntpe_launcher.py",
        description="NTPE 2.0 translation launcher product foundation (offline Stage 1)",
    )

    # Top-level subcommands
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Series subcommand
    series_parser = subparsers.add_parser("series", help="Series management")
    series_subparsers = series_parser.add_subparsers(dest="series_command", help="Series commands")

    # series create
    create_parser = series_subparsers.add_parser("create", help="Create new series")
    create_parser.add_argument("name", help="Series name")

    # series list
    series_subparsers.add_parser("list", help="List all series")

    # series status
    status_parser = series_subparsers.add_parser("status", help="Show series status")
    status_parser.add_argument("name", help="Series name")

    # series rename
    rename_parser = series_subparsers.add_parser("rename", help="Rename series")
    rename_parser.add_argument("old_name", help="Current series name")
    rename_parser.add_argument("new_name", help="New series name")

    # series add-book
    add_book_parser = series_subparsers.add_parser("add-book", help="Add book to series")
    add_book_parser.add_argument("name", help="Series name")
    add_book_parser.add_argument("source", type=Path, help="Source file path")
    add_book_parser.add_argument("--title", help="Book title")

    # series promote-book
    promote_parser = series_subparsers.add_parser("promote-book", help="Promote book to series")
    promote_parser.add_argument("name", help="Series name")
    promote_parser.add_argument("--book", type=int, required=True, help="Volume number")

    # series resume
    resume_parser = series_subparsers.add_parser("resume", help="Resume series/book")
    resume_parser.add_argument("name", help="Series name")
    resume_parser.add_argument("--book", type=int, help="Volume number to resume")

    # translate with series
    translate_parser = subparsers.add_parser("translate", help="Translate with series context")
    translate_parser.add_argument("--series", help="Series name")
    translate_parser.add_argument("--book", type=int, help="Volume number")
    translate_parser.add_argument("--dry-run", action="store_true", help="Dry-run mode")

    # Existing launcher commands (kept for backward compatibility)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--dry-run", action="store_true", help="validate and preview without translation execution")
    actions.add_argument("--validate-config", action="store_true", help="validate launcher configuration offline")
    actions.add_argument("--list-providers", action="store_true", help="list the static Provider catalog")
    actions.add_argument("--list-models", action="store_true", help="list the static Model catalog")
    actions.add_argument("--list-languages", action="store_true", help="list supported language selections")
    parser.add_argument("--config", type=Path, help="optional launcher configuration JSON file")

    return parser


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _validation_payload(result: Any) -> dict[str, Any]:
    validation = result
    return {
        "ready": validation.ready,
        "blocking_reasons": [asdict(issue) for issue in validation.blocking_reasons],
        "warnings": [asdict(issue) for issue in validation.warnings],
        "inspection": asdict(validation.inspection) if validation.inspection else None,
        "provider_requests": 0,
        "network_requests": 0,
        "translation_executions": 0,
    }


def _create_coordinator(output_root: Path) -> SeriesTranslationCoordinator:
    """Create a SeriesTranslationCoordinator with all required dependencies."""
    translation_runtime = TranslationRuntime(root=output_root)

    series_registry = SeriesRegistry(output_root)
    series_memory_store = SeriesMemoryStore(series_id="")  # Will be set per series
    series_entity_registry = SeriesEntityRegistry(series_id="", output_root=output_root)
    series_glossary = load_series_glossary("", output_root)  # Will be loaded per series
    series_knowledge = load_series_knowledge("", output_root)  # Will be loaded per series
    series_checkpoint_manager = SeriesCheckpointManager(
        output_root=output_root,
        series_registry=series_registry,
        series_memory_store=series_memory_store,
        series_entity_registry=series_entity_registry,
        series_glossary=series_glossary,
        series_knowledge=series_knowledge,
    )

    return SeriesTranslationCoordinator(
        output_root=output_root,
        series_registry=series_registry,
        series_memory_store=series_memory_store,
        series_entity_registry=series_entity_registry,
        series_glossary=series_glossary,
        series_knowledge=series_knowledge,
        series_checkpoint_manager=series_checkpoint_manager,
        translation_runtime=translation_runtime,
    )


def _run_gui() -> int:
    try:
        from ui.translation_launcher.app import run

        return run()
    except Exception as exc:
        if exc.__class__.__module__.startswith("tkinter") or exc.__class__.__name__ == "TclError":
            print("無法啟動圖形介面，請確認目前環境支援桌面視窗。", file=sys.stderr)
            return 2
        raise


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # Handle series commands
    if args.command == "series":
        output_root = Path.cwd() / "output"
        output_root.mkdir(parents=True, exist_ok=True)
        coordinator = _create_coordinator(output_root)

        if args.series_command == "create":
            cmd_series_create(coordinator, args.name)
            return 0
        elif args.series_command == "list":
            cmd_series_list(coordinator)
            return 0
        elif args.series_command == "status":
            cmd_series_status(coordinator, args.name)
            return 0
        elif args.series_command == "rename":
            cmd_series_rename(coordinator, args.old_name, args.new_name)
            return 0
        elif args.series_command == "add-book":
            cmd_series_add_book(coordinator, args.name, args.source, args.title)
            return 0
        elif args.series_command == "promote-book":
            cmd_series_promote_book(coordinator, args.name, args.book)
            return 0
        elif args.series_command == "resume":
            cmd_series_resume(coordinator, args.name, args.book)
            return 0
        else:
            _print_json({"status": "error", "message": f"Unknown series command: {args.series_command}"})
            return 1

    # Handle translate command with series context
    if args.command == "translate":
        if not args.series or not args.book:
            _print_json({"status": "error", "message": "Both --series and --book are required for series translation"})
            return 1
        output_root = Path.cwd() / "output"
        output_root.mkdir(parents=True, exist_ok=True)
        coordinator = _create_coordinator(output_root)
        cmd_translate_with_series(coordinator, args.series, args.book, dry_run=args.dry_run)
        return 0

    # Existing launcher commands (backward compatibility)
    if args.list_languages:
        _print_json(
            {
                "source_languages": [asdict(language) for language in source_languages()],
                "target_languages": [asdict(language) for language in target_languages()],
            }
        )
        return 0
    if args.list_providers:
        _print_json([asdict(provider) for provider in provider_catalog()])
        return 0
    if args.list_models:
        _print_json([asdict(model) for model in model_catalog()])
        return 0

    if args.dry_run or args.validate_config:
        try:
            config = load_launcher_config(args.config)
        except LauncherConfigError as exc:
            _print_json({"ready": False, "blocking_reasons": [str(exc)]})
            return 2
        if args.dry_run:
            result = build_dry_run(config)
            _print_json(result.details)
            return 0 if result.command.validation_result.ready else 1
        validation = validate_launcher_config(config)
        _print_json(_validation_payload(validation))
        return 0 if validation.ready else 1

    return _run_gui()


if __name__ == "__main__":
    raise SystemExit(main())