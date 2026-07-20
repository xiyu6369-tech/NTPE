from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LauncherConfig:
    input_path: str
    output_directory: str
    source_language: str
    target_language: str
    provider_id: str
    model_id: str
    translation_profile: str
    chunk_size: int
    api_timeout: int
    provider_attempts: int
    overwrite: bool
    resume_enabled: bool
    dry_run: bool


@dataclass(frozen=True, slots=True)
class LanguageDefinition:
    language_id: str
    display_name: str
    selectable: bool
    runtime_integrated: bool
    status_reason: str


@dataclass(frozen=True, slots=True)
class LanguageDetectionResult:
    language: str
    confidence: float
    signals: tuple[str, ...]
    sample_size: int
    ambiguous: bool


@dataclass(frozen=True, slots=True)
class InputFileInspection:
    path: str
    file_name: str
    file_size: int
    encoding: str
    readable: bool
    suspected_mojibake: bool
    sampled_bytes: int
    truncated_sample: bool
    detection: LanguageDetectionResult
    error_message: str = ""


@dataclass(frozen=True, slots=True)
class ProviderDefinition:
    provider_id: str
    display_name: str
    available: bool
    configured: bool
    requires_api_key: bool
    environment_variable: str
    supports_model_listing: bool
    network_required: bool
    status_reason: str


@dataclass(frozen=True, slots=True)
class ModelDefinition:
    model_id: str
    provider_id: str
    display_name: str
    enabled: bool
    experimental: bool
    recommended_for: tuple[str, ...]
    context_notes: str


@dataclass(frozen=True, slots=True)
class TranslationProfileDefinition:
    profile_id: str
    display_name: str
    available: bool
    runtime_value: str | None
    status_reason: str


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    field: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ready: bool
    blocking_reasons: tuple[ValidationIssue, ...]
    warnings: tuple[ValidationIssue, ...] = ()
    inspection: InputFileInspection | None = None


@dataclass(frozen=True, slots=True)
class CommandBuildResult:
    argument_list: tuple[str, ...]
    command_preview: str
    validation_result: ValidationResult


@dataclass(frozen=True, slots=True)
class DryRunResult:
    config: LauncherConfig
    command: CommandBuildResult
    details: dict[str, Any] = field(default_factory=dict)
