from __future__ import annotations

import os
from pathlib import Path
from typing import Any, TYPE_CHECKING

from core.ai_provider import ProviderRequest

from .basic_qa import BasicTranslationQA
from .context_intelligence import apply_context_intelligence
from .prompt_intelligence import apply_prompt_intelligence
from .provider_runtime import build_translation_provider_manager
from .utils import load_json, save_json, save_text, append_log, clean_translation_text, now_iso

if TYPE_CHECKING:
    from core.translation_runtime.models import TranslationRequest

# RM-5.3: Runtime Context Integration — wire TQI V72 adapter into default pipeline.
# Default-off, does not apply unless flagged in package metadata.
# Provider-Free, Network-Free, Output-Free. Fail-safe: any exception
# is logged and translation continues with the original prompt.
try:
    from core.translation_quality_integration_v72 import (
        QualityIntegrationFlags,
        apply_to_prompt_package as tqi_v72_apply_to_prompt_package,
    )
    _TQI_V72_ADAPTER_AVAILABLE = True
except ImportError:
    _TQI_V72_ADAPTER_AVAILABLE = False


class TranslationEngine:
    def __init__(self, root: str | Path, api_key: str | None = None):
        self.root = Path(root)
        self.logs_dir = self.root / "logs"
        self.cache_dir = self.root / "translation_cache"
        self.output_dir = self.root / "translated"

        self.qa = BasicTranslationQA()
        self.api_key = api_key

    def translate_package_file(self, package_path: str | Path) -> dict[str, Any]:
        package_path = Path(package_path)

        if not package_path.exists():
            return {
                "status": "failed",
                "error": f"Prompt Package 不存在：{package_path}",
            }

        package = load_json(package_path)
        return self.translate_package(package, package_path=package_path)

    def translate_package(self, package: dict, package_path: str | Path | None = None) -> dict[str, Any]:
        try:
            self._validate_package(package)
            package = apply_prompt_intelligence(package, package.get("source", {}).get("chunk_text", ""))
            package = apply_context_intelligence(package, package.get("source", {}).get("chunk_text", ""))

            # RM-5.3: Runtime Context Integration Phase 1 — wire TQI V72 adapter.
            # Default-off (flags only active when explicitly set in package metadata).
            # Provider-Free, Network-Free, Output-Free. Fail-safe: any exception
            # is logged and translation continues with the original prompt.
            if _TQI_V72_ADAPTER_AVAILABLE:
                try:
                    metadata = package.get("metadata") or {}
                    tqi_flags = QualityIntegrationFlags(
                        integration=bool(metadata.get("quality_integration_v72")),
                        character_memory=bool(metadata.get("quality_character_memory_v72")),
                        context_scene=bool(metadata.get("quality_context_scene_v72")),
                        naturalness=bool(metadata.get("quality_naturalness_v72")),
                        kill_switch=bool(metadata.get("quality_integration_kill_switch_v72")),
                    )
                    if tqi_flags.enabled:
                        package = tqi_v72_apply_to_prompt_package(package, flags=tqi_flags)
                        append_log(
                            self.logs_dir / "translation_engine_log.txt",
                            f"TQI V72 applied：{package['package_id']}",
                        )
                except Exception as exc:
                    append_log(
                        self.logs_dir / "translation_engine_error.txt",
                        f"TQI V72 degd：{package.get('package_id', '')}｜{type(exc).__name__}｜{exc}",
                    )

            model_profile = package["model_profile"]
            prompt = package["prompt"]

            provider_manager = build_translation_provider_manager(
                root=self.root,
                api_key=self.api_key,
                primary_model=model_profile["model"],
                api_url=self._get_api_url(package),
                timeout=self._get_timeout(package),
                rpm_limit=self._get_rpm_limit(package),
            )

            append_log(self.logs_dir / "translation_engine_log.txt", f"開始翻譯：{package['package_id']}")

            provider_response = provider_manager.complete(
                ProviderRequest(
                    prompt=prompt["user_prompt"],
                    model=model_profile["model"],
                    temperature=model_profile.get("temperature", 0.15),
                    max_tokens=model_profile.get("max_output_tokens", 4000),
                    metadata={
                        "system_prompt": prompt["system_prompt"],
                        "top_p": model_profile.get("top_p", 0.85),
                        "package_id": package["package_id"],
                        "runtime": "translation_engine_v3",
                    },
                )
            )

            raw_text = provider_response.text
            translation = clean_translation_text(raw_text)
            qa_result = self.qa.check(package, translation)

            output_path = self._build_output_path(package)
            cache_path = self._build_cache_path(package)

            save_text(output_path, translation)

            result = {
                "status": "success",
                "package_id": package["package_id"],
                "translated_at": now_iso(),
                "output_path": str(output_path),
                "cache_path": str(cache_path),
                "qa": qa_result,
                "package_path": str(package_path) if package_path else "",
                "provider": provider_response.to_dict(),
            }

            save_json(cache_path, {
                "result": result,
                "translation": translation,
                "package": package,
            })

            append_log(
                self.logs_dir / "translation_engine_log.txt",
                f"完成：{package['package_id']} -> {output_path}"
            )

            if qa_result.get("issues"):
                append_log(
                    self.logs_dir / "translation_engine_log.txt",
                    f"QA warning：{package['package_id']} issues={len(qa_result['issues'])}"
                )

            return result

        except Exception as e:
            error_result = {
                "status": "failed",
                "package_id": package.get("package_id", "") if isinstance(package, dict) else "",
                "error": str(e),
                "failed_at": now_iso(),
            }

            append_log(
                self.logs_dir / "translation_engine_error.txt",
                f"{error_result['package_id']}｜{error_result['error']}"
            )

            return error_result

    def translate_package_from_request(
        self,
        request: TranslationRequest,
        *,
        source_text: str = "",
        chunk_index: int = 0,
        file_name: str = "chunk.txt",
    ) -> dict[str, Any]:
        """RM-6.3.0: Translate from an immutable TranslationRequest.

        The Translation Request carries the fully assembled prompt from
        the Runtime pipeline.  The Engine does NOT construct, assemble,
        or modify the prompt; it only executes the provider call and QA.

        Provider API, output format, and caching behavior remain identical
        to the legacy translate_package() path.
        """
        from core.translation_runtime.models import TranslationRequest as _TR
        assert isinstance(request, _TR), "request must be a TranslationRequest"

        try:
            metadata = request.metadata
            runtime_snapshot = request.runtime_snapshot

            model_profile = metadata.get("model_profile", {})
            if not isinstance(model_profile, dict):
                model_profile = {}

            model = model_profile.get("model")
            if not model:
                model = str(model_profile) if model_profile else ""

            system_prompt = metadata.get("system_prompt", "")
            user_prompt = request.prompt

            source_payload = metadata.get("source") or {}
            chunk_text = source_text or source_payload.get("chunk_text", "")
            char_count = source_payload.get("char_count") or (len(chunk_text) if chunk_text else 0)

            package_id = metadata.get("package_id") or request.snapshot_id or request.prompt_hash or ""
            provider_manager = build_translation_provider_manager(
                root=self.root,
                api_key=self.api_key,
                primary_model=model,
                api_url=self._get_api_url_from_request(metadata),
                timeout=self._get_timeout_from_request(runtime_snapshot, char_count),
                rpm_limit=self._get_rpm_limit_from_request(metadata),
            )

            append_log(self.logs_dir / "translation_engine_log.txt",
                       f"開始翻譯（request）：{package_id} hash={request.prompt_hash}")

            provider_response = provider_manager.complete(
                ProviderRequest(
                    prompt=user_prompt,
                    model=model,
                    temperature=model_profile.get("temperature", 0.15),
                    max_tokens=model_profile.get("max_output_tokens", 4000),
                    metadata={
                        "system_prompt": system_prompt,
                        "top_p": model_profile.get("top_p", 0.85),
                        "package_id": package_id,
                        "runtime": "translation_engine_v3_rm630",
                        "prompt_hash": request.prompt_hash,
                        "snapshot_id": request.snapshot_id,
                        "section_count": request.section_count,
                        "token_count": request.token_count,
                    },
                )
            )

            raw_text = provider_response.text
            translation = clean_translation_text(raw_text)

            qa_package = {
                "source": {"chunk_text": chunk_text},
                "package_id": package_id,
            }
            qa_result = self.qa.check(qa_package, translation)

            output_path = self._build_output_path_from_request(file_name, chunk_index)
            cache_path = self._build_cache_path_from_request(file_name, chunk_index)

            save_text(output_path, translation)

            result = {
                "status": "success",
                "package_id": package_id,
                "translated_at": now_iso(),
                "output_path": str(output_path),
                "cache_path": str(cache_path),
                "qa": qa_result,
                "package_path": "",
                "provider": provider_response.to_dict(),
                "prompt_hash": request.prompt_hash,
                "snapshot_id": request.snapshot_id,
                "request_version": request.version,
            }

            save_json(cache_path, {
                "result": result,
                "translation": translation,
                "request": request.to_dict(),
                "runtime_snapshot": runtime_snapshot,
            })

            append_log(
                self.logs_dir / "translation_engine_log.txt",
                f"完成（request）：{package_id} -> {output_path}"
            )

            if qa_result.get("issues"):
                append_log(
                    self.logs_dir / "translation_engine_log.txt",
                    f"QA（request）：{package_id} issues={len(qa_result['issues'])}"
                )

            return result

        except Exception as e:
            err_result = {
                "status": "failed",
                "package_id": request.snapshot_id or request.prompt_hash or "",
                "error": str(e),
                "failed_at": now_iso(),
                "prompt_hash": request.prompt_hash,
            }
            append_log(
                self.logs_dir / "translation_engine_error.txt",
                f"request::{err_result['package_id']}::{err_result['error']}"
            )
            return err_result

    def _get_rpm_limit(self, package: dict) -> int:
        return 40

    def _get_rpm_limit_from_request(self, metadata: dict) -> int:
        return 40

    def _get_api_url_from_request(self, metadata: dict) -> str:
        return metadata.get("api_url") or "https://integrate.api.nvidia.com/v1/chat/completions"

    def _get_timeout_from_request(
        self, runtime_snapshot: dict, char_count: int
    ) -> int:
        current_timeout = os.environ.get("NTPE_CURRENT_API_TIMEOUT")
        value = current_timeout or os.environ.get("NTPE_API_TIMEOUT")
        try:
            base_timeout = max(5, int(float(value))) if value else 60
        except ValueError:
            base_timeout = 60

        if current_timeout:
            return base_timeout

        attempt = 1
        try:
            attempt = int(runtime_snapshot.get("provider_attempt", 1) or 1)
        except Exception:
            pass

        if os.environ.get("NTPE_API_TIMEOUT_EXPLICIT") == "1":
            return base_timeout
        if attempt == 1 and 0 < char_count <= 700:
            return min(base_timeout, int(os.environ.get("NTPE_SHORT_CHUNK_FIRST_TIMEOUT", "120")))
        return base_timeout

    def _build_output_path_from_request(self, file_name: str, chunk_index: int) -> Path:
        file_stem = Path(file_name).stem
        return self.output_dir / f"{file_stem}_chunk_{chunk_index:06d}_zh.txt"

    def _build_cache_path_from_request(self, file_name: str, chunk_index: int) -> Path:
        file_stem = Path(file_name).stem
        return self.cache_dir / f"{file_stem}_chunk_{chunk_index:06d}_result.json"

    def _validate_package(self, package: dict) -> None:
        required = ["package_id", "model_profile", "prompt", "source", "session"]
        for key in required:
            if key not in package:
                raise ValueError(f"Prompt Package 缺少欄位：{key}")

        if not package["prompt"].get("system_prompt"):
            raise ValueError("Prompt Package 缺少 system_prompt")

        if not package["prompt"].get("user_prompt"):
            raise ValueError("Prompt Package 缺少 user_prompt")

    def _get_api_url(self, package: dict) -> str:
        # Prompt Package v1.0 沒有保存 api_url，所以這裡使用 NVIDIA 預設。
        return "https://integrate.api.nvidia.com/v1/chat/completions"

    def _get_timeout(self, package: dict) -> int:
        # TER-v1.8: adaptive first-attempt timeout for short literary chunks.
        # A short Smoke_Set request should not burn the full 180s before retrying
        # when the provider worker hangs.  The environment value is still used as
        # the upper bound for later attempts and long chunks.
        current_timeout = os.environ.get("NTPE_CURRENT_API_TIMEOUT")
        value = current_timeout or os.environ.get("NTPE_API_TIMEOUT")
        try:
            base_timeout = max(5, int(float(value))) if value else 60
        except ValueError:
            base_timeout = 60

        # TER-v2.4: the TXT runtime already calculates the exact per-attempt
        # provider timeout and passes it through NTPE_CURRENT_API_TIMEOUT.  Do
        # not apply the short-chunk clamp a second time inside the engine.
        if current_timeout:
            return base_timeout

        source_len = 0
        attempt = 1
        try:
            source_len = int(package.get("source", {}).get("char_count", 0) or 0)
            attempt = int(package.get("runtime", {}).get("provider_attempt", 1) or 1)
        except Exception:
            pass

        if os.environ.get("NTPE_API_TIMEOUT_EXPLICIT") == "1":
            return base_timeout
        if attempt == 1 and 0 < source_len <= 700:
            return min(base_timeout, int(os.environ.get("NTPE_SHORT_CHUNK_FIRST_TIMEOUT", "120")))
        return base_timeout

    def _build_output_path(self, package: dict) -> Path:
        session = package["session"]
        file_stem = Path(session["file_name"]).stem
        chunk_index = int(session["chunk_index"])
        return self.output_dir / f"{file_stem}_chunk_{chunk_index:06d}_zh.txt"

    def _build_cache_path(self, package: dict) -> Path:
        session = package["session"]
        file_stem = Path(session["file_name"]).stem
        chunk_index = int(session["chunk_index"])
        return self.cache_dir / f"{file_stem}_chunk_{chunk_index:06d}_result.json"
