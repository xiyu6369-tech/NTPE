from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import LauncherConfigError
from .models import LauncherConfig, TranslationProfileDefinition


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = ROOT / "config/launcher_product_defaults.json"

SOURCE_LANGUAGE_IDS = ("auto", "ko", "ja", "en")
TARGET_LANGUAGE_IDS = ("zh-Hant",)
CHUNK_SIZE_BOUNDS = (100, 4000)
API_TIMEOUT_BOUNDS = (10, 600)
PROVIDER_ATTEMPT_BOUNDS = (1, 5)

TRANSLATION_PROFILES = (
    TranslationProfileDefinition("literary", "Literary", True, "literary", "integrated"),
    TranslationProfileDefinition("balanced", "Balanced", True, "balanced", "integrated"),
    TranslationProfileDefinition("faithful", "Faithful", False, None, "not_yet_integrated"),
)

_BASE_CONFIG: dict[str, Any] = {
    "input_path": "",
    "output_directory": "output",
    "source_language": "auto",
    "target_language": "zh-Hant",
    "provider_id": "nvidia",
    "model_id": "meta/llama-3.2-90b-vision-instruct",
    "translation_profile": "literary",
    "chunk_size": 600,
    "api_timeout": 180,
    "provider_attempts": 2,
    "overwrite": False,
    "resume_enabled": True,
    "dry_run": False,
}


def translation_profiles() -> tuple[TranslationProfileDefinition, ...]:
    return TRANSLATION_PROFILES


def _read_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LauncherConfigError(f"Configuration file not found: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LauncherConfigError(f"Unable to read configuration file: {path}") from exc
    if not isinstance(payload, dict):
        raise LauncherConfigError("Launcher configuration must be a JSON object.")
    unknown = sorted(set(payload) - set(_BASE_CONFIG))
    if unknown:
        raise LauncherConfigError("Unknown launcher configuration fields: " + ", ".join(unknown))
    return payload


def _validate_types(payload: dict[str, Any]) -> None:
    string_fields = (
        "input_path",
        "output_directory",
        "source_language",
        "target_language",
        "provider_id",
        "model_id",
        "translation_profile",
    )
    integer_fields = ("chunk_size", "api_timeout", "provider_attempts")
    boolean_fields = ("overwrite", "resume_enabled", "dry_run")
    for field_name in string_fields:
        if not isinstance(payload[field_name], str):
            raise LauncherConfigError(f"{field_name} must be a string.")
    for field_name in integer_fields:
        if isinstance(payload[field_name], bool) or not isinstance(payload[field_name], int):
            raise LauncherConfigError(f"{field_name} must be an integer.")
    for field_name in boolean_fields:
        if not isinstance(payload[field_name], bool):
            raise LauncherConfigError(f"{field_name} must be true or false.")


def load_launcher_config(
    path: str | Path | None = None,
    *,
    overrides: dict[str, Any] | None = None,
) -> LauncherConfig:
    payload = dict(_BASE_CONFIG)
    defaults_path = DEFAULT_CONFIG_PATH
    if defaults_path.is_file():
        payload.update(_read_object(defaults_path))
    if path is not None:
        payload.update(_read_object(Path(path)))
    if overrides:
        unknown = sorted(set(overrides) - set(_BASE_CONFIG))
        if unknown:
            raise LauncherConfigError("Unknown launcher configuration fields: " + ", ".join(unknown))
        payload.update(overrides)
    _validate_types(payload)
    return LauncherConfig(**payload)
