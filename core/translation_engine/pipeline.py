"""Translation pipeline layer."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import time

from .strategy import TranslationStrategy


@dataclass
class TranslationPipelineContext:
    segment: Any
    index: int = 0
    payload: Dict[str, Any] = field(default_factory=dict)
    prompt_package: Dict[str, Any] = field(default_factory=dict)
    knowledge_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment": self.segment,
            "index": self.index,
            "payload": dict(self.payload),
            "prompt_package": dict(self.prompt_package),
            "knowledge_context": dict(self.knowledge_context),
            "metadata": dict(self.metadata),
        }


class TranslationPipeline:
    def __init__(
        self,
        translator: Optional[Callable[[Any, Dict[str, Any]], Any]] = None,
        knowledge_runtime: Any = None,
        prompt_builder: Any = None,
        strategy: Optional[TranslationStrategy] = None,
    ):
        self.translator = translator or self._default_translator
        self.knowledge_runtime = knowledge_runtime
        self.prompt_builder = prompt_builder
        self.strategy = strategy or TranslationStrategy()

    def build_context(self, segment: Any, index: int = 0, payload: Optional[Dict[str, Any]] = None) -> TranslationPipelineContext:
        base_payload = dict(payload or {})
        knowledge_context: Dict[str, Any] = {}
        if self.knowledge_runtime is not None and hasattr(self.knowledge_runtime, "before_segment"):
            try:
                knowledge_context = self.knowledge_runtime.before_segment(segment=segment, payload=base_payload)
            except TypeError:
                knowledge_context = self.knowledge_runtime.before_segment(segment, base_payload)
        prompt_package = self.build_prompt_package(segment, knowledge_context, base_payload)
        return TranslationPipelineContext(segment=segment, index=index, payload=base_payload, prompt_package=prompt_package, knowledge_context=knowledge_context, metadata={"strategy": self.strategy.to_dict()})

    def build_prompt_package(self, segment: Any, knowledge_context: Optional[Dict[str, Any]] = None, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.prompt_builder is not None:
            for method in ("build", "build_prompt_package", "create"):
                if hasattr(self.prompt_builder, method):
                    result = getattr(self.prompt_builder, method)(segment, knowledge_context or {}, payload or {})
                    if isinstance(result, dict):
                        return result
                    return {"prompt": str(result), "source": segment, "knowledge": knowledge_context or {}}
        return {
            "type": "translation_prompt_package",
            "source": segment,
            "prompt": str(segment),
            "knowledge": knowledge_context or {},
            "payload": dict(payload or {}),
        }

    def execute(self, context: TranslationPipelineContext) -> Dict[str, Any]:
        started = time.time()
        raw = self.translator(context.segment, context.to_dict())
        translation = self._extract_translation(raw)
        result = {
            "type": "translation_pipeline_result",
            "index": context.index,
            "source": context.segment,
            "translation": translation,
            "raw_output": raw,
            "prompt_package": context.prompt_package,
            "knowledge_context": context.knowledge_context,
            "duration_seconds": time.time() - started,
        }
        if self.knowledge_runtime is not None and hasattr(self.knowledge_runtime, "after_segment"):
            try:
                result["knowledge_after"] = self.knowledge_runtime.after_segment(segment=context.segment, result=result)
            except TypeError:
                result["knowledge_after"] = self.knowledge_runtime.after_segment(context.segment, result)
        return result

    def process(self, segment: Any, index: int = 0, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.execute(self.build_context(segment, index=index, payload=payload))

    def _extract_translation(self, raw: Any) -> str:
        if isinstance(raw, dict):
            for key in ("translation", "text", "output", "result"):
                if key in raw:
                    return str(raw[key])
        return str(raw or "")

    def _default_translator(self, segment: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"translation": str(segment), "status": "translated", "context": context}

    def manifest(self) -> Dict[str, Any]:
        return {"type": "translation_pipeline", "strategy": self.strategy.to_dict(), "has_knowledge_runtime": self.knowledge_runtime is not None}
