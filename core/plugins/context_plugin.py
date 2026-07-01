from __future__ import annotations

from typing import Any

from core.context.memory_engine import ContextMemoryEngine

from .plugin_base import PluginBase
from .plugin_context import PluginContext


class ContextMemoryPlugin(PluginBase):
    name = "context_memory"
    stage = "context"
    priority = 10

    def setup(self, context: PluginContext) -> None:
        self.engine = ContextMemoryEngine(context.root)

    def run(self, payload: dict[str, Any], context: PluginContext) -> dict[str, Any]:
        result = dict(payload)

        previous_tail = result.get("previous_tail", "")
        result["context"] = self.engine.build_context(previous_tail=previous_tail)

        return result

    def update_after_chunk(
        self,
        *,
        file_name: str,
        chunk_index: int,
        source_text: str,
        translation_text: str = "",
    ) -> dict:
        return self.engine.update_after_chunk(
            file_name=file_name,
            chunk_index=chunk_index,
            source_text=source_text,
            translation_text=translation_text,
        )