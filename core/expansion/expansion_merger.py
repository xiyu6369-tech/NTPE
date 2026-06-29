from __future__ import annotations

import re


class ExpansionMerger:
    """
    將補足後的段落合併回原譯文。
    """

    def split_paragraphs(self, text: str) -> list[str]:
        text = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            return []
        return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    def merge(self, original_translation: str, expanded_paragraphs: dict[int, str]) -> str:
        paragraphs = self.split_paragraphs(original_translation)

        for idx, new_text in expanded_paragraphs.items():
            pos = idx - 1
            if pos < 0:
                continue

            if pos < len(paragraphs):
                paragraphs[pos] = new_text.strip()
            else:
                while len(paragraphs) < pos:
                    paragraphs.append("")
                paragraphs.append(new_text.strip())

        return "\n\n".join(p for p in paragraphs if p.strip()).strip() + "\n"
