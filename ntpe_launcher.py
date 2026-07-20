from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from core.launcher_product.config import LauncherConfigError, load_launcher_config
from core.launcher_product.dry_run import build_dry_run
from core.launcher_product.languages import source_languages, target_languages
from core.launcher_product.model_catalog import model_catalog
from core.launcher_product.provider_catalog import provider_catalog
from core.launcher_product.validation import validate_launcher_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ntpe_launcher.py",
        description="NTPE 2.0 translation launcher product foundation (offline Stage 1)",
    )
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


def _validation_payload(result: object) -> dict[str, object]:
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
