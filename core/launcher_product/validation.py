from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from .config import (
    API_TIMEOUT_BOUNDS,
    CHUNK_SIZE_BOUNDS,
    PROVIDER_ATTEMPT_BOUNDS,
    SOURCE_LANGUAGE_IDS,
    TARGET_LANGUAGE_IDS,
    translation_profiles,
)
from .languages import inspect_text_file
from .model_catalog import get_model
from .models import LauncherConfig, ValidationIssue, ValidationResult
from .provider_catalog import get_provider


def _issue(code: str, message: str, field: str) -> ValidationIssue:
    return ValidationIssue(code=code, message=message, field=field)


def _validate_output_directory(value: str) -> ValidationIssue | None:
    if not value.strip():
        return _issue("output_directory_invalid", "請選擇有效的輸出資料夾。", "output_directory")
    path = Path(value)
    if path.exists():
        if not path.is_dir():
            return _issue("output_directory_invalid", "輸出位置必須是資料夾。", "output_directory")
        if not os.access(path, os.W_OK):
            return _issue("output_directory_invalid", "輸出資料夾目前無法寫入。", "output_directory")
        return None
    parent = path.parent if path.parent != Path("") else Path.cwd()
    if not parent.exists() or not parent.is_dir() or not os.access(parent, os.W_OK):
        return _issue("output_directory_invalid", "輸出資料夾的上層路徑不存在或無法寫入。", "output_directory")
    return None


def validate_launcher_config(
    config: LauncherConfig,
    *,
    environment: Mapping[str, str] | None = None,
) -> ValidationResult:
    blockers: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    inspection = None

    if not config.input_path.strip():
        blockers.append(_issue("input_file_missing", "請選擇要翻譯的 TXT 小說檔案。", "input_path"))
    else:
        input_path = Path(config.input_path)
        if not input_path.exists():
            blockers.append(_issue("input_file_missing", "找不到選取的輸入檔案。", "input_path"))
        elif input_path.is_dir():
            blockers.append(_issue("input_path_is_directory", "輸入位置必須是檔案，不可以是資料夾。", "input_path"))
        elif input_path.suffix.lower() != ".txt":
            blockers.append(_issue("unsupported_file_type", "Stage 1 目前只支援 TXT 檔案。", "input_path"))
        else:
            inspection = inspect_text_file(input_path)
            if not inspection.readable:
                blockers.append(_issue("unreadable_encoding", inspection.error_message, "input_path"))
            elif inspection.suspected_mojibake:
                blockers.append(_issue("suspected_mojibake", "檔案內容可能包含亂碼，請確認文字編碼。", "input_path"))

    output_issue = _validate_output_directory(config.output_directory)
    if output_issue:
        blockers.append(output_issue)

    if config.source_language not in SOURCE_LANGUAGE_IDS:
        blockers.append(_issue("unsupported_source_language", "不支援選取的來源語言。", "source_language"))
    elif config.source_language == "auto" and inspection and inspection.readable:
        detected = inspection.detection
        if detected.language == "unknown" or detected.ambiguous:
            blockers.append(_issue("source_language_unresolved", "無法可靠判斷來源語言，請手動選擇。", "source_language"))
        elif detected.language != "ko":
            blockers.append(_issue("source_language_not_integrated", "此來源語言可辨識，但尚未接入現有翻譯執行層。", "source_language"))
    elif config.source_language in {"ja", "en"}:
        blockers.append(_issue("source_language_not_integrated", "此來源語言尚未接入現有翻譯執行層。", "source_language"))

    if config.target_language not in TARGET_LANGUAGE_IDS:
        blockers.append(_issue("unsupported_target_language", "Stage 1 目前只支援繁體中文目標語言。", "target_language"))

    provider = get_provider(config.provider_id, environment)
    if provider is None:
        blockers.append(_issue("unknown_provider", "找不到選取的 Provider。", "provider_id"))
    else:
        if not provider.available:
            blockers.append(_issue("provider_not_integrated", "此 Provider 已列入 catalog，但尚未接入 Launcher。", "provider_id"))
        if provider.requires_api_key and not provider.configured:
            blockers.append(_issue("provider_unconfigured", f"請先設定 {provider.environment_variable}。", "provider_id"))

    model = get_model(config.model_id)
    if model is None:
        blockers.append(_issue("unknown_model", "找不到選取的 Model。", "model_id"))
    else:
        if model.provider_id != config.provider_id:
            blockers.append(_issue("model_provider_mismatch", "選取的 Model 不屬於此 Provider。", "model_id"))
        if not model.enabled:
            blockers.append(_issue("model_not_enabled", "此 Model 目前只列入 catalog，尚不可執行。", "model_id"))

    profiles = {profile.profile_id: profile for profile in translation_profiles()}
    profile = profiles.get(config.translation_profile)
    if profile is None:
        blockers.append(_issue("unsupported_profile", "找不到選取的翻譯模式。", "translation_profile"))
    elif not profile.available:
        blockers.append(_issue("profile_not_integrated", "此翻譯模式尚未接入現有 Runtime。", "translation_profile"))

    if not CHUNK_SIZE_BOUNDS[0] <= config.chunk_size <= CHUNK_SIZE_BOUNDS[1]:
        blockers.append(_issue("invalid_chunk_size", "Chunk size 必須介於 100 與 4000。", "chunk_size"))
    if not API_TIMEOUT_BOUNDS[0] <= config.api_timeout <= API_TIMEOUT_BOUNDS[1]:
        blockers.append(_issue("invalid_timeout", "Timeout 必須介於 10 與 600 秒。", "api_timeout"))
    if not PROVIDER_ATTEMPT_BOUNDS[0] <= config.provider_attempts <= PROVIDER_ATTEMPT_BOUNDS[1]:
        blockers.append(_issue("invalid_provider_attempts", "Provider attempts 必須介於 1 與 5。", "provider_attempts"))
    if config.overwrite:
        blockers.append(_issue("overwrite_not_integrated", "現有 TXT CLI 沒有 overwrite 參數，Stage 1 不會虛構此功能。", "overwrite"))

    if inspection and inspection.readable and config.source_language not in {"auto", inspection.detection.language}:
        warnings.append(_issue("source_language_mismatch", "手動來源語言與離線偵測結果不同。", "source_language"))

    return ValidationResult(
        ready=not blockers,
        blocking_reasons=tuple(blockers),
        warnings=tuple(warnings),
        inspection=inspection,
    )
