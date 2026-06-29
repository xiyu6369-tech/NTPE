from __future__ import annotations

from pathlib import Path

from core.quality.coverage_expansion_analyzer import CoverageExpansionAnalyzer


class ExpansionPlanner:
    """
    根據段落級 coverage 分析建立補足計畫。
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.analyzer = CoverageExpansionAnalyzer(root=self.root)

    def plan(self, source_text: str, translation_text: str) -> dict:
        analysis = self.analyzer.analyze(source_text, translation_text)

        tasks = []
        for target in analysis["targets"]:
            tasks.append({
                "paragraph_index": target["paragraph_index"],
                "source": target["source"],
                "current_translation": target["translation"],
                "source_length": target["source_length"],
                "translation_length": target["translation_length"],
                "ratio": target["ratio"],
                "hints": target["hints"],
                "goal": "補足偏短譯文，保留已正確內容，補回省略的動作、心理、場景、比喻與停頓。",
            })

        return {
            "passed": analysis["passed"],
            "source_paragraphs": analysis["source_paragraphs"],
            "translation_paragraphs": analysis["translation_paragraphs"],
            "task_count": len(tasks),
            "tasks": tasks,
            "analysis": analysis,
        }
