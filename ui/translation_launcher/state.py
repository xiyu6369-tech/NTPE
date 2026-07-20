from __future__ import annotations

from dataclasses import dataclass

from core.launcher_product.config import load_launcher_config


@dataclass(frozen=True, slots=True)
class LauncherWindowModel:
    title: str
    input_path: str
    output_directory: str
    source_language: str
    target_language: str
    provider_id: str
    model_id: str
    translation_profile: str
    chunk_size: int
    api_timeout: int
    resume_enabled: bool
    overwrite: bool
    validate_enabled: bool
    preview_enabled: bool
    start_enabled: bool
    start_disabled_reason: str


def build_window_model() -> LauncherWindowModel:
    config = load_launcher_config()
    return LauncherWindowModel(
        title="NTPE 2.0 Translation Launcher",
        input_path=config.input_path,
        output_directory=config.output_directory,
        source_language=config.source_language,
        target_language=config.target_language,
        provider_id=config.provider_id,
        model_id=config.model_id,
        translation_profile=config.translation_profile,
        chunk_size=config.chunk_size,
        api_timeout=config.api_timeout,
        resume_enabled=config.resume_enabled,
        overwrite=config.overwrite,
        validate_enabled=True,
        preview_enabled=True,
        start_enabled=False,
        start_disabled_reason="Translation execution is not enabled in Stage 1.",
    )
