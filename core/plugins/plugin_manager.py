from __future__ import annotations

from pathlib import Path

from core.runtime import RuntimeManager

from .plugin_context import PluginContext
from .plugin_registry import PluginRegistry
from .context_plugin import ContextMemoryPlugin
from .prompt_plugin import PromptBuilderPlugin
from .quality_plugin import QualityPlugin
from .narrative_plugin import NarrativePlugin


class PipelinePluginManager:
    """
    NTPE v1.2 Foundation-03.6

    負責替 Pipeline 建立與註冊標準 Plugins。
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.runtime = RuntimeManager(self.root)
        self.context = PluginContext(
            root=self.root,
            runtime=self.runtime,
        )
        self.registry = PluginRegistry(self.context)

    def register_default_plugins(self) -> PluginRegistry:
        self.registry.register(ContextMemoryPlugin())
        self.registry.register(NarrativePlugin())
        self.registry.register(PromptBuilderPlugin())
        self.registry.register(QualityPlugin())
        return self.registry

    def build_registry(self) -> PluginRegistry:
        return self.register_default_plugins()