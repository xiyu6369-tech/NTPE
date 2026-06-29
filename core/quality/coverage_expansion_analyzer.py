from __future__ import annotations

import json
import re
from pathlib import Path


class CoverageExpansionAnalyzer:
    """
    TQF-05.2 Coverage Expansion Analyzer

    用途：
    - 將 source / translation 對齊為段落。
    - 找出翻譯偏短、疑似被摘要化的段落。
    - 產生 expansion targets，交給 Expansion Engine 局部補足。
    """

    DEFAULT_THRESHOLDS = {
        "paragraph_min_ratio": 0.72,
        "paragraph_warning_ratio": 0.82,
        "max_targets_per_run": 8,
    }

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root else None
        self.thresholds = dict(self.DEFAULT_THRESHOLDS)

        if self.root:
            path = self.root / "rules" / "expansion_rules.json"
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8-sig"))
                    self.thresholds.update(data.get("thresholds", {}))
                except Exception:
                    pass

    def analyze(self, source_text: str, translation_text: str) -> dict:
        source_paragraphs = self._split_paragraphs(source_text)
        translation_paragraphs = self._split_paragraphs(translation_text)

        pairs = []
        targets = []

        max_len = max(len(source_paragraphs), len(translation_paragraphs))

        for i in range(max_len):
            source = source_paragraphs[i] if i < len(source_paragraphs) else ""
            translation = translation_paragraphs[i] if i < len(translation_paragraphs) else ""

            source_len = len(source)
            translation_len = len(translation)
            ratio = translation_len / source_len if source_len else 1.0

            status = "ok"
            severity = "info"

            if source and not translation:
                status = "missing"
                severity = "error"
            elif source_len >= 60 and ratio < self.thresholds["paragraph_min_ratio"]:
                status = "too_short"
                severity = "warning"
            elif source_len >= 60 and ratio < self.thresholds["paragraph_warning_ratio"]:
                status = "slightly_short"
                severity = "info"

            pair = {
                "paragraph_index": i + 1,
                "source": source,
                "translation": translation,
                "source_length": source_len,
                "translation_length": translation_len,
                "ratio": round(ratio, 4),
                "status": status,
                "severity": severity,
                "hints": self._build_hints(source),
            }

            pairs.append(pair)

            if status in ["missing", "too_short"]:
                targets.append(pair)

        # 優先處理最短 ratio 的段落，但限制數量，避免一次重翻太久。
        targets.sort(key=lambda x: (x["ratio"], -x["source_length"]))
        max_targets = int(self.thresholds["max_targets_per_run"])
        limited_targets = targets[:max_targets]

        return {
            "source_paragraphs": len(source_paragraphs),
            "translation_paragraphs": len(translation_paragraphs),
            "target_count": len(limited_targets),
            "all_target_count": len(targets),
            "pairs": pairs,
            "targets": limited_targets,
            "passed": len(targets) == 0,
        }

    def _split_paragraphs(self, text: str) -> list[str]:
        text = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            return []
        return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    def _build_hints(self, source: str) -> list[str]:
        hints = []

        if any(k in source for k in ["예감", "기분", "생각", "불길", "우울"]):
            hints.append("保留心理描寫與情緒層次。")
        if any(k in source for k in ["비", "궂은", "소리 없이", "희미하게"]):
            hints.append("保留天氣、聲音、空間氛圍。")
        if any(k in source for k in ["떨어져", "굴렀다", "두드리며", "비켜섰다", "멈췄다"]):
            hints.append("保留動作順序與畫面感。")
        if any(k in source for k in ["역병신", "다를 바 없는"]):
            hints.append("保留比喻，不可攤平成普通敘述。")
        if any(k in source for k in ["말했다", "물었다", "중얼거렸다", "노려보았다"]):
            hints.append("保留對話語氣與動作銜接。")

        if not hints:
            hints.append("補足被壓縮的原文資訊，維持自然繁體中文小說語感。")

        return hints
