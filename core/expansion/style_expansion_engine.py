from __future__ import annotations

import json
from pathlib import Path

from core.translation_engine.nvidia_client import NvidiaClient
from .expansion_planner import ExpansionPlanner
from .expansion_prompt_builder import ExpansionPromptBuilder
from .expansion_merger import ExpansionMerger


class StyleExpansionEngine:
    """
    TQF-05.2 Coverage-Aware Style Expansion Engine

    流程：
    1. 分析 source / translation 的段落級 coverage。
    2. 找出偏短段落。
    3. 只對偏短段落建立補足 Prompt。
    4. 呼叫 NVIDIA API 補足該段。
    5. 合併回原譯文。
    """

    def __init__(self, root: str | Path, api_key: str | None = None):
        self.root = Path(root)
        self.planner = ExpansionPlanner(self.root)
        self.prompt_builder = ExpansionPromptBuilder()
        self.merger = ExpansionMerger()
        self.client = NvidiaClient(api_key=api_key)

    def expand(
        self,
        *,
        source_text: str,
        translation_text: str,
        file_name: str,
        chunk_index: int,
        model: str = "meta/llama-3.3-70b-instruct",
        max_output_tokens: int = 1600,
    ) -> dict:
        plan = self.planner.plan(source_text, translation_text)

        if plan["passed"] or not plan["tasks"]:
            return {
                "status": "no_action",
                "plan": plan,
                "translation": translation_text,
                "expanded": {},
            }

        expanded = {}

        for task in plan["tasks"]:
            prompt = self.prompt_builder.build(task, file_name=file_name, chunk_index=chunk_index)

            text = self.client.chat(
                model=model,
                system_prompt=prompt["system_prompt"],
                user_prompt=prompt["user_prompt"],
                temperature=0.12,
                top_p=0.85,
                max_tokens=max_output_tokens,
            ).strip()

            expanded[int(task["paragraph_index"])] = text

        merged = self.merger.merge(translation_text, expanded)

        return {
            "status": "expanded",
            "plan": plan,
            "translation": merged,
            "expanded": expanded,
        }
