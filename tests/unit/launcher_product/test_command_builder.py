from __future__ import annotations

from dataclasses import replace

from core.launcher_product.command_builder import build_translation_command, powershell_quote
from core.launcher_product.config import load_launcher_config


def _config(input_path: str, output_path: str):
    return replace(
        load_launcher_config(),
        input_path=input_path,
        output_directory=output_path,
        source_language="ko",
        dry_run=True,
    )


def test_command_output_is_deterministic(tmp_path) -> None:
    source = tmp_path / "novel.txt"
    source.write_text("한국어 문장입니다.", encoding="utf-8")
    config = _config(str(source), str(tmp_path / "output"))
    first = build_translation_command(config, environment={"NVIDIA_API_KEY": "x"})
    second = build_translation_command(config, environment={"NVIDIA_API_KEY": "x"})
    assert first == second


def test_command_contains_only_existing_txt_flags() -> None:
    result = build_translation_command(_config("novel.txt", "output"), environment={"NVIDIA_API_KEY": "x"})
    allowed_flags = {
        "--chunk-size", "--model", "--provider-attempts", "--profile", "--api-timeout", "--no-resume", "--dry-run"
    }
    assert {argument for argument in result.argument_list if argument.startswith("--")} <= allowed_flags
    assert "--provider" not in result.argument_list
    assert "--overwrite" not in result.argument_list


def test_paths_with_spaces_and_unicode_remain_single_arguments() -> None:
    config = _config(r"C:\小說 資料\第一章.txt", r"C:\輸出 資料")
    result = build_translation_command(config, environment={"NVIDIA_API_KEY": "x"})
    assert config.input_path in result.argument_list
    assert config.output_directory in result.argument_list
    assert "'C:\\小說 資料\\第一章.txt'" in result.command_preview


def test_shell_metacharacters_are_quoted_not_executed() -> None:
    dangerous = r"C:\books\novel;Remove-Item important.txt"
    result = build_translation_command(_config(dangerous, "output"), environment={"NVIDIA_API_KEY": "x"})
    assert dangerous in result.argument_list
    assert powershell_quote(dangerous) in result.command_preview
    assert powershell_quote("a'b") == "'a''b'"
