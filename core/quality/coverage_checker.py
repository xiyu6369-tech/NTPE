from __future__ import annotations

import json
from pathlib import Path

from .coverage_analyzer import CoverageAnalyzer


class CoverageChecker:
    """
    TQF-03 Coverage Checker

    專門檢查：
    - 譯文是否過短
    - 段落是否被大幅壓縮
    - 句子是否明顯不足
    """

    DEFAULT_THRESHOLDS = {
        "min_length_ratio_warning": 0.70,
        "min_length_ratio_error": 0.62,
        "min_paragraph_ratio_warning": 0.70,
        "min_paragraph_ratio_error": 0.55,
    }

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root else None
        self.analyzer = CoverageAnalyzer()
        self.thresholds = dict(self.DEFAULT_THRESHOLDS)

        if self.root:
            path = self.root / "rules" / "coverage_rules.json"
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8-sig"))
                    self.thresholds.update(data.get("thresholds", {}))
                except Exception:
                    pass

    def check(self, source_text: str, translation_text: str) -> dict:
        metrics = self.analyzer.analyze(source_text, translation_text)
        issues = []

        length_ratio = metrics["length_ratio"]
        paragraph_ratio = metrics["paragraph_ratio"]

        if length_ratio < self.thresholds["min_length_ratio_error"]:
            issues.append({
                "severity": "error",
                "type": "coverage_too_short",
                "message": f"譯文長度比例過低，疑似摘要或漏翻：ratio={length_ratio}",
            })
        elif length_ratio < self.thresholds["min_length_ratio_warning"]:
            issues.append({
                "severity": "warning",
                "type": "coverage_short",
                "message": f"譯文偏短，需檢查是否漏翻：ratio={length_ratio}",
            })

        if paragraph_ratio < self.thresholds["min_paragraph_ratio_error"]:
            issues.append({
                "severity": "error",
                "type": "paragraph_compression_error",
                "message": (
                    "段落壓縮過度："
                    f"source={metrics['source_paragraphs']}, translation={metrics['translation_paragraphs']}, "
                    f"ratio={paragraph_ratio}"
                ),
            })
        elif paragraph_ratio < self.thresholds["min_paragraph_ratio_warning"]:
            issues.append({
                "severity": "warning",
                "type": "paragraph_compression_warning",
                "message": (
                    "段落數偏少："
                    f"source={metrics['source_paragraphs']}, translation={metrics['translation_paragraphs']}, "
                    f"ratio={paragraph_ratio}"
                ),
            })

        score = self.score(metrics, issues)

        return {
            "passed": not any(i["severity"] == "error" for i in issues),
            "score": score,
            "metrics": metrics,
            "issues": issues,
        }

    def score(self, metrics: dict, issues: list[dict]) -> int:
        score = 100

        length_ratio = metrics["length_ratio"]
        paragraph_ratio = metrics["paragraph_ratio"]

        if length_ratio < 0.62:
            score -= 35
        elif length_ratio < 0.70:
            score -= 20
        elif length_ratio < 0.80:
            score -= 10

        if paragraph_ratio < 0.55:
            score -= 40
        elif paragraph_ratio < 0.70:
            score -= 25
        elif paragraph_ratio < 0.85:
            score -= 10

        # error 額外扣分
        score -= sum(10 for i in issues if i["severity"] == "error")
        score -= sum(3 for i in issues if i["severity"] == "warning")

        return max(score, 0)
