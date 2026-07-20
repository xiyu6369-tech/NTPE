from __future__ import annotations

from collections.abc import Mapping

from core.launcher_product.command_builder import build_translation_command
from core.launcher_product.languages import inspect_text_file
from core.launcher_product.models import CommandBuildResult, InputFileInspection, LauncherConfig, ValidationResult
from core.launcher_product.validation import validate_launcher_config


class LauncherController:
    def __init__(self, environment: Mapping[str, str] | None = None) -> None:
        self._environment = environment

    def inspect_input(self, path: str) -> InputFileInspection:
        return inspect_text_file(path)

    def validate(self, config: LauncherConfig) -> ValidationResult:
        return validate_launcher_config(config, environment=self._environment)

    def preview(self, config: LauncherConfig) -> CommandBuildResult:
        return build_translation_command(config, environment=self._environment)

    @staticmethod
    def start_translation() -> None:
        raise RuntimeError("Translation execution is not enabled in Stage 1.")
