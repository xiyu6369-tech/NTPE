from __future__ import annotations

from pathlib import Path
from typing import Any

from .plugin_manager import PipelinePluginManager


class PipelinePluginAdapter:
    """
    NTPE v1.2 Foundation-03.6 Batch-3

    用途：
    讓 pipeline_v1.py 可以逐步改用 Plugin Registry，
    但不用一次重寫整個 ProductionPipelineV1。
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.manager = PipelinePluginManager(self.root)
        self.registry = self.manager.build_registry()

    def build_context(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.registry.run_stage("context", payload)

    def build_narrative(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.registry.run_stage("narrative", payload)

    def build_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.registry.run_stage("prompt", payload)

    def run_quality(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.registry.run_stage("quality", payload)

    def run_pre_translation(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload = self.build_context(payload)
        payload = self.build_narrative(payload)
        payload = self.build_prompt(payload)
        return payload

    def run_post_translation(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.run_quality(payload)