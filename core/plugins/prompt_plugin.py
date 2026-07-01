from __future__ import annotations

from typing import Any

from core.prompt_builder.prompt_builder import PromptBuilder

from .plugin_base import PluginBase
from .plugin_context import PluginContext


class PromptBuilderPlugin(PluginBase):
    name = "prompt_builder"
    stage = "prompt"
    priority = 10

    def setup(self, context: PluginContext) -> None:
        self.builder = PromptBuilder(root=context.root)

    def run(self, payload: dict[str, Any], context: PluginContext) -> dict[str, Any]:
        result = dict(payload)

        required = [
            "chunk_text",
            "file_name",
            "chunk_index",
            "chunk_total",
            "session_id",
        ]

        missing = [key for key in required if key not in result]
        if missing:
            raise ValueError(f"PromptBuilderPlugin missing payload keys: {missing}")

        package = self.builder.build(
            chunk_text=result["chunk_text"],
            file_name=result["file_name"],
            chunk_index=result["chunk_index"],
            chunk_total=result["chunk_total"],
            session_id=result["session_id"],
            context=result.get("context"),
        )

        result["prompt_package"] = package
        result["prompt"] = package.get("prompt", {})
        return result