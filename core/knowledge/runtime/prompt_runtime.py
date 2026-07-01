"""Foundation-08.2 Knowledge Prompt Runtime."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..contracts import KnowledgeQuery
from .context_runtime import KnowledgeContextRuntime


class KnowledgePromptRuntime:
    """Attach Knowledge Runtime context to prompt packages."""

    version = "foundation-08.2"

    def __init__(self, context_runtime: Optional[KnowledgeContextRuntime] = None):
        self.context_runtime = context_runtime or KnowledgeContextRuntime()

    def attach(
        self,
        prompt_package: Optional[Dict[str, Any]] = None,
        segment: Any = None,
        query: Optional[KnowledgeQuery] = None,
    ) -> Dict[str, Any]:
        next_package = dict(prompt_package or {})
        components = list(next_package.get("context_components", []))
        components.append(self.context_runtime.build_context(segment=segment, query=query))
        next_package["context_components"] = components
        next_package["knowledge_runtime"] = {
            "version": self.version,
            "attached": True,
        }
        return next_package

    def attach_to_prompt_package(self, prompt_package: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.attach(prompt_package, **kwargs)


__all__ = ["KnowledgePromptRuntime"]
