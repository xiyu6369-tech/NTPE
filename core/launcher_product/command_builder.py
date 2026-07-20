from __future__ import annotations

import re
from collections.abc import Mapping

from .config import translation_profiles
from .models import CommandBuildResult, LauncherConfig
from .validation import validate_launcher_config


_POWERSHELL_SAFE = re.compile(r"^[A-Za-z0-9_./:\\-]+$")


def powershell_quote(argument: str) -> str:
    if argument and _POWERSHELL_SAFE.fullmatch(argument):
        return argument
    return "'" + argument.replace("'", "''") + "'"


def build_translation_command(
    config: LauncherConfig,
    *,
    environment: Mapping[str, str] | None = None,
) -> CommandBuildResult:
    validation = validate_launcher_config(config, environment=environment)
    profiles = {profile.profile_id: profile for profile in translation_profiles()}
    profile = profiles.get(config.translation_profile)
    runtime_profile = profile.runtime_value if profile and profile.runtime_value else config.translation_profile
    arguments = [
        "python",
        "launcher_translate.py",
        "txt",
        config.input_path,
        config.output_directory,
        "--chunk-size",
        str(config.chunk_size),
        "--model",
        config.model_id,
        "--provider-attempts",
        str(config.provider_attempts),
        "--profile",
        runtime_profile,
        "--api-timeout",
        str(config.api_timeout),
    ]
    if not config.resume_enabled:
        arguments.append("--no-resume")
    if config.dry_run:
        arguments.append("--dry-run")
    preview = " ".join(powershell_quote(argument) for argument in arguments)
    return CommandBuildResult(tuple(arguments), preview, validation)
