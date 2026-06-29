from __future__ import annotations

import re


class CoverageAnalyzer:
    """
    TQF-03 Coverage Analyzer

    用途：
    - 比較 source / translation 的長度、段落、句子與對話覆蓋程度。
    - 不呼叫 AI，只做可重複的靜態檢查。
    """

    def analyze(self, source_text: str, translation_text: str) -> dict:
        source_text = source_text or ""
        translation_text = translation_text or ""

        source_paragraphs = self.split_paragraphs(source_text)
        translation_paragraphs = self.split_paragraphs(translation_text)

        source_sentences = self.split_sentences(source_text)
        translation_sentences = self.split_sentences(translation_text)

        source_len = len(source_text.strip())
        translation_len = len(translation_text.strip())

        length_ratio = translation_len / source_len if source_len else 0.0
        paragraph_ratio = len(translation_paragraphs) / len(source_paragraphs) if source_paragraphs else 0.0
        sentence_ratio = len(translation_sentences) / len(source_sentences) if source_sentences else 0.0

        source_dialogue = self.count_dialogue_like(source_text)
        translation_dialogue = self.count_dialogue_like(translation_text)
        dialogue_ratio = translation_dialogue / source_dialogue if source_dialogue else 1.0

        return {
            "source_length": source_len,
            "translation_length": translation_len,
            "length_ratio": round(length_ratio, 4),
            "source_paragraphs": len(source_paragraphs),
            "translation_paragraphs": len(translation_paragraphs),
            "paragraph_ratio": round(paragraph_ratio, 4),
            "source_sentences": len(source_sentences),
            "translation_sentences": len(translation_sentences),
            "sentence_ratio": round(sentence_ratio, 4),
            "source_dialogue_count": source_dialogue,
            "translation_dialogue_count": translation_dialogue,
            "dialogue_ratio": round(dialogue_ratio, 4),
        }

    def split_paragraphs(self, text: str) -> list[str]:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    def split_sentences(self, text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []

        # 韓文、中文、英文句末標點
        parts = re.split(r"(?<=[。！？!?\.])\s+|(?<=[。！？!?\.])", text)
        return [p.strip() for p in parts if p.strip()]

    def count_dialogue_like(self, text: str) -> int:
        # 韓文原文可能用 " 或 '；譯文應該用「」
        return len(re.findall(r"[\"'「」『』]", text))
