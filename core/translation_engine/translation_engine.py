from __future__ import annotations

from pathlib import Path
from typing import Any

from .nvidia_client import NvidiaClient
from .basic_qa import BasicTranslationQA
from .utils import load_json, save_json, save_text, append_log, clean_translation_text, now_iso


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

            model_profile = package["model_profile"]
            prompt = package["prompt"]

            client = NvidiaClient(
                api_key=self.api_key,
                api_url=self._get_api_url(package),
                timeout=self._get_timeout(package),
                rpm_limit=self._get_rpm_limit(package),
            )

            append_log(self.logs_dir / "translation_engine_log.txt", f"開始翻譯：{package['package_id']}")

            raw_text = client.chat(
                model=model_profile["model"],
                system_prompt=prompt["system_prompt"],
                user_prompt=prompt["user_prompt"],
                temperature=model_profile.get("temperature", 0.15),
                top_p=model_profile.get("top_p", 0.85),
                max_tokens=model_profile.get("max_output_tokens", 4000),
            )

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
        return 180

    def _get_rpm_limit(self, package: dict) -> int:
        return 40

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
