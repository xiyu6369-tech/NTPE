from __future__ import annotations

from typing import Any, Dict
from .engine_bridge import TranslationQualityBridge


class ProviderQualityBridge:
    def __init__(self, quality_bridge: TranslationQualityBridge | None = None):
        self.quality_bridge = quality_bridge or TranslationQualityBridge()

    def evaluate_provider_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        source = response.get("source_text", "")
        text = response.get("text", response.get("translated_text", ""))
        result = self.quality_bridge.validate_translation(source, text, response.get("metadata", {}))
        output = dict(response)
        output["quality"] = result.to_dict()
        return output
