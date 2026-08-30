from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from core.launcher_product.config import load_launcher_config
from ui.translation_launcher.controller import LauncherController
from ui.translation_launcher.state import build_window_model


ROOT = Path(__file__).resolve().parents[3]


def test_app_imports_without_creating_window() -> None:
    from ui.translation_launcher import app

    assert app.TranslationLauncherApp is not None
    assert build_window_model().start_enabled is False


def test_controller_validation_and_preview_are_offline(tmp_path) -> None:
    source = tmp_path / "소설.txt"
    source.write_text("그는 천천히 고개를 들고 창밖을 바라보았다.", encoding="utf-8")
    output = tmp_path / "translated"
    config = replace(
        load_launcher_config(),
        input_path=str(source),
        output_directory=str(output),
        source_language="auto",
        dry_run=True,
    )
    controller = LauncherController({"NVIDIA_API_KEY": "configured"})
    validation = controller.validate(config)
    preview = controller.preview(config)
    assert validation.ready is True
    assert preview.validation_result.ready is True
    assert preview.argument_list[:3] == ("python", "launcher_translate.py", "txt")
    assert output.exists() is False
    assert not list(tmp_path.rglob("*resume*"))


def test_cli_dry_run_does_not_create_output_or_resume(tmp_path) -> None:
    source = tmp_path / "novel.txt"
    source.write_text("그녀는 조용히 책을 덮었다.", encoding="utf-8")
    output = tmp_path / "output"
    config_path = tmp_path / "launcher.json"
    config = {
        "input_path": str(source),
        "output_directory": str(output),
        "source_language": "auto",
        "target_language": "zh-Hant",
        "provider_id": "nvidia",
        "model_id": "meta/llama-3.2-90b-vision-instruct",
        "translation_profile": "literary",
        "chunk_size": 600,
        "api_timeout": 180,
        "provider_attempts": 2,
        "resume_enabled": True,
        "overwrite": False,
        "dry_run": True,
    }
    config_path.write_text(json.dumps(config), encoding="utf-8")
    environment = {**os.environ, "NVIDIA_API_KEY": "configured"}
    result = subprocess.run(
        [sys.executable, str(ROOT / "ntpe_launcher.py"), "--dry-run", "--config", str(config_path)],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ready"] is True
    assert payload["generated_command"].endswith("--dry-run")
    assert output.exists() is False
    assert not list(tmp_path.rglob("*resume*"))
