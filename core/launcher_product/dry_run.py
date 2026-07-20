from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from .command_builder import build_translation_command
from .models import DryRunResult, LauncherConfig


def build_dry_run(
    config: LauncherConfig,
    *,
    environment: Mapping[str, str] | None = None,
) -> DryRunResult:
    dry_config = replace(config, dry_run=True)
    command = build_translation_command(dry_config, environment=environment)
    inspection = command.validation_result.inspection
    detected_language = inspection.detection.language if inspection else "unknown"
    details: dict[str, Any] = {
        "input": dry_config.input_path,
        "output": dry_config.output_directory,
        "detected_source_language": detected_language,
        "target_language": dry_config.target_language,
        "provider": dry_config.provider_id,
        "model": dry_config.model_id,
        "profile": dry_config.translation_profile,
        "chunk_size": dry_config.chunk_size,
        "timeout": dry_config.api_timeout,
        "resume": dry_config.resume_enabled,
        "overwrite": dry_config.overwrite,
        "generated_command": command.command_preview,
        "ready": command.validation_result.ready,
        "blocking_reasons": [issue.message for issue in command.validation_result.blocking_reasons],
    }
    return DryRunResult(config=dry_config, command=command, details=details)
