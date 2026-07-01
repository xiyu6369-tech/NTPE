from __future__ import annotations

from typing import Any, Dict
from .contract import QualityContext
from .pipeline import QualityPipeline
from .report import QualityReport


class TranslationQualityBridge:
    def __init__(self, pipeline: QualityPipeline | None = None):
        self.pipeline = pipeline or QualityPipeline()

    def validate_translation(self, source_text: str, translated_text: str, metadata: Dict[str, Any] | None = None):
        context = QualityContext(source_text=source_text, translated_text=translated_text, metadata=metadata or {})
        return self.pipeline.run(context)

    def attach_quality_report(self, payload: Dict[str, Any], result) -> Dict[str, Any]:
        payload = dict(payload)
        payload["quality_report"] = QualityReport(result).summary()
        return payload
