from __future__ import annotations

from typing import Any, Dict


class MockModelAdapter:
    """Deterministic adapter for tests and offline development."""

    adapter_id = "mock-model-adapter"
    model = "mock/translation-runtime"

    def translate(self, prompt_package: Dict[str, Any]) -> Dict[str, Any]:
        text = prompt_package.get("source_text") or prompt_package.get("prompt_text") or ""
        if prompt_package.get("force_error"):
            raise RuntimeError("mock model error")
        return {
            "model": self.model,
            "output_text": f"[translated] {text}".strip(),
            "raw": {"adapter_id": self.adapter_id},
        }

    def manifest(self) -> Dict[str, Any]:
        return {
            "kind": "ntpe.model_adapter",
            "adapter_id": self.adapter_id,
            "model": self.model,
            "version": "06.5",
        }


class TranslationExecutorAdapter:
    def __init__(self, executor: Any):
        self.executor = executor

    def execute(self, job: Dict[str, Any], segment: Dict[str, Any], context_bundle: Dict[str, Any] | None = None, prompt_package: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return self.executor.execute_segment(job, segment, context_bundle=context_bundle, prompt_package=prompt_package)

    def manifest(self) -> Dict[str, Any]:
        return self.executor.manifest()
