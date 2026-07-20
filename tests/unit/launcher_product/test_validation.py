from __future__ import annotations

from dataclasses import replace

from core.launcher_product.config import load_launcher_config
from core.launcher_product.validation import validate_launcher_config


def _valid_config(tmp_path):
    source = tmp_path / "novel.txt"
    source.write_text("그는 문을 열고 천천히 안으로 들어갔다.", encoding="utf-8")
    return replace(
        load_launcher_config(),
        input_path=str(source),
        output_directory=str(tmp_path / "translated"),
        source_language="auto",
        dry_run=True,
    )


def _codes(result) -> set[str]:
    return {issue.code for issue in result.blocking_reasons}


def test_valid_config(tmp_path) -> None:
    result = validate_launcher_config(_valid_config(tmp_path), environment={"NVIDIA_API_KEY": "configured"})
    assert result.ready is True


def test_missing_input_is_blocked(tmp_path) -> None:
    config = replace(_valid_config(tmp_path), input_path=str(tmp_path / "missing.txt"))
    assert "input_file_missing" in _codes(validate_launcher_config(config, environment={"NVIDIA_API_KEY": "x"}))


def test_invalid_output_is_blocked(tmp_path) -> None:
    output_file = tmp_path / "output.txt"
    output_file.write_text("not a directory", encoding="utf-8")
    config = replace(_valid_config(tmp_path), output_directory=str(output_file))
    assert "output_directory_invalid" in _codes(validate_launcher_config(config, environment={"NVIDIA_API_KEY": "x"}))


def test_unconfigured_provider_is_blocked(tmp_path) -> None:
    result = validate_launcher_config(_valid_config(tmp_path), environment={})
    assert "provider_unconfigured" in _codes(result)


def test_model_provider_mismatch_is_blocked(tmp_path) -> None:
    config = replace(_valid_config(tmp_path), model_id="gemini-2.5-flash")
    assert "model_provider_mismatch" in _codes(validate_launcher_config(config, environment={"NVIDIA_API_KEY": "x"}))


def test_invalid_chunk_size_is_blocked(tmp_path) -> None:
    config = replace(_valid_config(tmp_path), chunk_size=99)
    assert "invalid_chunk_size" in _codes(validate_launcher_config(config, environment={"NVIDIA_API_KEY": "x"}))


def test_invalid_timeout_is_blocked(tmp_path) -> None:
    config = replace(_valid_config(tmp_path), api_timeout=601)
    assert "invalid_timeout" in _codes(validate_launcher_config(config, environment={"NVIDIA_API_KEY": "x"}))


def test_unsupported_target_language_is_blocked(tmp_path) -> None:
    config = replace(_valid_config(tmp_path), target_language="en")
    assert "unsupported_target_language" in _codes(validate_launcher_config(config, environment={"NVIDIA_API_KEY": "x"}))


def test_catalogued_but_unintegrated_features_are_blocked(tmp_path) -> None:
    config = replace(
        _valid_config(tmp_path),
        provider_id="gemini",
        model_id="gemini-2.5-flash",
        translation_profile="faithful",
        source_language="ja",
    )
    codes = _codes(validate_launcher_config(config, environment={"GEMINI_API_KEY": "x"}))
    assert {"provider_not_integrated", "model_not_enabled", "profile_not_integrated", "source_language_not_integrated"} <= codes
