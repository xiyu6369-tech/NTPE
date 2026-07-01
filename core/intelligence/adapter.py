"""Adapter layer for injecting intelligence data into Runtime/Prompt packages."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .consistency import ConsistencyContract
from .memory_store import IntelligenceMemoryStore


class IntelligenceAdapter:
    """Runtime-safe adapter for translation intelligence.

    The adapter does not assume a concrete Runtime class. It returns plain dict
    payloads that existing Runtime Manifest or Prompt Package components can attach
    without breaking older callers.
    """

    def __init__(self, store: Optional[IntelligenceMemoryStore] = None) -> None:
        self.store = store or IntelligenceMemoryStore()
        self.consistency = ConsistencyContract()

    def build_prompt_context(self) -> Dict[str, Any]:
        snapshot = self.store.build_snapshot().to_dict()
        return {
            "type": "translation_intelligence_context",
            "version": "foundation-07.0",
            "characters": snapshot["characters"],
            "glossary": snapshot["glossary"],
            "narrative": snapshot["narrative"],
            "scenes": snapshot["scenes"],
        }

    def build_runtime_manifest_component(self) -> Dict[str, Any]:
        snapshot = self.store.build_snapshot().to_dict()
        return {
            "name": "translation_intelligence_contract",
            "version": "foundation-07.0",
            "enabled": True,
            "manifest": snapshot["manifest"],
        }

    def attach_to_manifest(self, manifest: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        next_manifest: Dict[str, Any] = dict(manifest or {})
        components = list(next_manifest.get("components", []))
        components.append(self.build_runtime_manifest_component())
        next_manifest["components"] = components
        return next_manifest

    def attach_to_prompt_package(self, prompt_package: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        next_package: Dict[str, Any] = dict(prompt_package or {})
        context_components = list(next_package.get("context_components", []))
        context_components.append(self.build_prompt_context())
        next_package["context_components"] = context_components
        return next_package

    def validate_output(self, output_text: str) -> Dict[str, Any]:
        snapshot = self.store.build_snapshot()
        glossary_entries = list(self.store._glossary.values())  # Internal read for contract validation.
        target_names = [item.get("target_name", "") for item in snapshot.characters]
        issues = []
        issues.extend(self.consistency.validate_glossary_output(output_text, glossary_entries))
        issues.extend(self.consistency.validate_character_output(output_text, target_names))
        return {
            "passed": not any(issue.severity in {"error"} for issue in issues),
            "issue_count": len(issues),
            "issues": [issue.to_dict() for issue in issues],
        }
