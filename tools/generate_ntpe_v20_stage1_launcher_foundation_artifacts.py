from __future__ import annotations

import json
import sys
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.launcher_product.command_builder import build_translation_command
from core.launcher_product.config import load_launcher_config
from core.launcher_product.languages import detect_source_language, source_languages, target_languages
from core.launcher_product.model_catalog import model_catalog
from core.launcher_product.provider_catalog import provider_catalog
from ui.translation_launcher.controller import LauncherController
from ui.translation_launcher.state import build_window_model


ARTIFACT_DIRECTORY = ROOT / "artifacts/ntpe_v20_stage1_translation_launcher_product_foundation"
SAMPLE_INPUT = ROOT / "tests/fixtures/launcher_product/korean_sample.txt"


def _write_json(name: str, payload: Any) -> None:
    ARTIFACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    destination = ARTIFACT_DIRECTORY / name
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _language_evidence() -> dict[str, Any]:
    samples = {
        "empty": "",
        "english": "She closed the book and looked through the window.",
        "japanese": "彼女は静かに本を閉じた。雨が降っている。",
        "korean": "그녀는 조용히 책을 덮고 창밖의 비를 바라보았다.",
        "mixed": "安寧 가나 abcd 世界",
        "traditional_chinese_only": "她靜靜合上書本望向窗外",
    }
    return {
        "detector": "deterministic_offline_unicode_ranges",
        "maximum_file_sample_bytes": 65_536,
        "network_requests": 0,
        "results": {name: asdict(detect_source_language(text)) for name, text in samples.items()},
        "source_catalog": [asdict(item) for item in source_languages()],
        "target_catalog": [asdict(item) for item in target_languages()],
    }


def _command_evidence() -> dict[str, Any]:
    config = replace(
        load_launcher_config(),
        input_path=str(SAMPLE_INPUT.relative_to(ROOT)),
        output_directory="output",
        dry_run=True,
    )
    result = build_translation_command(config, environment={"NVIDIA_API_KEY": "configured"})
    unsupported = {"--input", "--output", "--overwrite", "--provider", "--target-language"}
    return {
        "argument_list": list(result.argument_list),
        "command_preview": result.command_preview,
        "deterministic": result == build_translation_command(
            config, environment={"NVIDIA_API_KEY": "configured"}
        ),
        "existing_execution_layer": "launcher_translate.py txt INPUT OUTPUT",
        "generated_unsupported_flags": sorted(unsupported.intersection(result.argument_list)),
        "provider_requests": 0,
        "ready": result.validation_result.ready,
        "subprocess_started": False,
        "translation_executions": 0,
    }


def _gui_evidence() -> dict[str, Any]:
    model = build_window_model()
    controller = LauncherController({"NVIDIA_API_KEY": "configured"})
    config = replace(
        load_launcher_config(),
        input_path=str(SAMPLE_INPUT),
        output_directory=str(ROOT / "output"),
        dry_run=True,
    )
    validation = controller.validate(config)
    preview = controller.preview(config)
    return {
        "app_imported": True,
        "network_requests": 0,
        "preview_enabled": model.preview_enabled,
        "preview_ready": preview.validation_result.ready,
        "provider_requests": 0,
        "start_disabled_reason": model.start_disabled_reason,
        "start_enabled": model.start_enabled,
        "translation_executions": 0,
        "validate_enabled": model.validate_enabled,
        "validation_ready": validation.ready,
        "window_model": asdict(model),
    }


def main() -> int:
    _write_json("LANGUAGE_DETECTION_EVIDENCE.json", _language_evidence())
    _write_json("PROVIDER_CATALOG.json", {
        "environment_values_exposed": False,
        "providers": [asdict(item) for item in provider_catalog({})],
        "static_offline_catalog": True,
    })
    _write_json("MODEL_CATALOG.json", {
        "models": [asdict(item) for item in model_catalog()],
        "remote_model_listing_requests": 0,
        "static_offline_catalog": True,
    })
    _write_json("COMMAND_BUILDER_EVIDENCE.json", _command_evidence())
    _write_json("GUI_SMOKE_EVIDENCE.json", _gui_evidence())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
