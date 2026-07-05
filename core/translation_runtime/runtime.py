from __future__ import annotations

from pathlib import Path
from typing import Iterable, Any

from core.translation_engine.translation_engine import TranslationEngine


class TranslationRuntime:
    """
    NTPE 1.2 Professional formal Translation Runtime facade.

    This layer is intentionally additive: it keeps NTPE 1.1 LTS APIs intact while
    making launcher, TXT, and batch translation share one official runtime entry.
    """

    version = "1.2-professional-stage-01"

    def __init__(self, root: str | Path | None = None, api_key: str | None = None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[2]
        self.api_key = api_key
        self.engine = TranslationEngine(root=self.root, api_key=api_key)

    def translate_package_file(self, package_path: str | Path) -> dict[str, Any]:
        return self.engine.translate_package_file(package_path)

    def translate_package(self, package: dict, package_path: str | Path | None = None) -> dict[str, Any]:
        return self.engine.translate_package(package, package_path=package_path)

    def translate_txt(self, options: Any) -> dict[str, Any]:
        # Lazy import prevents circular imports and preserves the frozen LTS module.
        from lts.txt_translation_runtime import translate_txt
        return translate_txt(options, root=self.root)

    def translate_batch(self, options: Any) -> dict[str, Any]:
        from lts.batch_translation_runtime import translate_batch
        return translate_batch(options, root=self.root)

    def main_txt(self, argv: Iterable[str] | None = None) -> int:
        from lts.txt_translation_runtime import parse_args
        options = parse_args(argv)
        result = self.translate_txt(options)
        print("NTPE 1.2 Professional TXT Translation Runtime")
        print("=============================================")
        print(f"status: {result['status']}")
        print(f"input: {result.get('input', '')}")
        print(f"output: {result.get('output', '')}")
        print(f"chunks: {result.get('chunk_total', 0)}")
        print(f"resume_state: {result.get('resume_state', '')}")
        return 0 if result.get("status") == "success" else 1

    def main_batch(self, argv: Iterable[str] | None = None) -> int:
        from lts.batch_translation_runtime import parse_args
        options = parse_args(argv)
        result = self.translate_batch(options)
        print("NTPE 1.2 Professional Batch Translation Runtime")
        print("================================================")
        print(f"status: {result['status']}")
        print(f"input_dir: {result.get('input_dir', '')}")
        print(f"output_dir: {result.get('output_dir', '')}")
        summary = result.get("summary", {})
        print(f"files: {summary.get('total_files', 0)}")
        print(f"success: {summary.get('success', 0)}")
        print(f"failed: {summary.get('failed', 0)}")
        return 0 if result.get("status") == "success" else 1


def main_txt(argv: Iterable[str] | None = None) -> int:
    return TranslationRuntime().main_txt(argv)


def main_batch(argv: Iterable[str] | None = None) -> int:
    return TranslationRuntime().main_batch(argv)
