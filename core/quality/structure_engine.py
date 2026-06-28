from __future__ import annotations

import json
import re
from pathlib import Path


class DocumentStructureEngine:
    """
    TQF-01 Document Structure Engine

    Purpose:
    - Detect structural lines such as work titles and chapter titles.
    - Prevent titles like "패션 1" from being translated as body text.
    - Provide structure metadata to Prompt Builder and Prompt Package.
    """

    NUMBER_ZH = {
        "0": "零", "1": "一", "2": "二", "3": "三", "4": "四",
        "5": "五", "6": "六", "7": "七", "8": "八", "9": "九",
        "10": "十",
    }

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.rules_path = self.root / "rules" / "document_structure_rules.json"
        self.rules = self._load_rules()

    def analyze(self, text: str, *, file_name: str = "", chunk_index: int = 1) -> dict:
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        first_idx = self._first_non_empty_line_index(lines)

        blocks = []
        title = None
        warnings = []

        if first_idx is not None:
            first_line = lines[first_idx].strip()
            detected = self._detect_title(first_line)
            if detected:
                title = detected
                title["line_index"] = first_idx
                title["original_line"] = first_line
                blocks.append(title)

                # Mark remaining non-empty lines as body for metadata only.
                body_start = first_idx + 1
                while body_start < len(lines) and not lines[body_start].strip():
                    body_start += 1
                if body_start < len(lines):
                    blocks.append({
                        "type": "body",
                        "line_index": body_start,
                        "note": "Body text starts here after detected title.",
                    })

        if title is None and chunk_index == 1:
            warnings.append("No title detected in first chunk.")

        return {
            "enabled": True,
            "module": "TQF-01 Document Structure Engine",
            "version": "1.0",
            "file_name": file_name,
            "chunk_index": chunk_index,
            "has_title": title is not None,
            "title": title,
            "blocks": blocks,
            "rules": self.rules.get("rules", []),
            "warnings": warnings,
        }

    def _load_rules(self) -> dict:
        if not self.rules_path.exists():
            return {"work_titles": [], "title_patterns": [], "separators": [], "rules": []}
        return json.loads(self.rules_path.read_text(encoding="utf-8-sig"))

    def _first_non_empty_line_index(self, lines: list[str]) -> int | None:
        for i, line in enumerate(lines):
            if line.strip():
                return i
        return None

    def _detect_title(self, line: str) -> dict | None:
        # Locked work title: 패션 1 -> 《PASSION》第一卷
        m = re.fullmatch(r"패션\s*(\d+)", line)
        if m:
            number = m.group(1)
            return {
                "type": "work_title",
                "level": 1,
                "source": line,
                "source_title": "패션",
                "number": number,
                "target": self._format_passion_title(number),
                "locked": True,
                "rule": "作品標題：패션 固定譯為 PASSION，不可翻成『時尚』；標題不可併入正文。",
            }

        # Generic chapter/section titles.
        for pat in self.rules.get("title_patterns", []):
            try:
                if re.fullmatch(pat.get("regex", ""), line):
                    return {
                        "type": pat.get("type", "title"),
                        "level": pat.get("level", 1),
                        "source": line,
                        "target": line,
                        "locked": False,
                        "rule": "章節或段落標題，必須獨立保留，不可併入正文。",
                    }
            except re.error:
                continue

        if line in self.rules.get("separators", []):
            return {
                "type": "separator",
                "level": 0,
                "source": line,
                "target": line,
                "locked": True,
                "rule": "分隔線必須獨立保留。",
            }

        return None

    def _format_passion_title(self, number: str) -> str:
        number_zh = self.NUMBER_ZH.get(number, number)
        return f"《PASSION》第{number_zh}卷"
