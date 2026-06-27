from __future__ import annotations

import re
from typing import Iterable, List, Optional


class FormatEngine:
    """NTPE Format Engine.

    Goal: preserve the Step002-style novel layout:
    - paragraph blocks separated by one blank line
    - no giant wall of text
    - no one-sentence-per-line formatting
    - dialogue uses 「」
    - if the model collapses paragraphs, rebuild paragraph breaks by source structure
    """

    def format_chunk(self, text: str, source: Optional[str] = None) -> str:
        text = self._normalize_newlines(text)
        text = self._normalize_quotes(text)
        text = self._normalize_spaces(text)
        text = self._normalize_paragraphs(text)

        if source:
            text = self._restore_source_paragraph_shape(source, text)

        text = self._split_overlong_paragraphs(text)
        text = self._normalize_paragraphs(text)
        return text.strip()

    def format_document(self, parts: Iterable[str]) -> str:
        clean_parts: List[str] = []
        for part in parts:
            formatted = self.format_chunk(part)
            if formatted:
                clean_parts.append(formatted)
        return "\n\n".join(clean_parts).strip() + "\n"

    def _normalize_newlines(self, text: str) -> str:
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _normalize_spaces(self, text: str) -> str:
        lines = []
        for line in text.split("\n"):
            line = re.sub(r"[ \t　]+", " ", line).strip()
            lines.append(line)
        text = "\n".join(lines)
        text = re.sub(r"\s+([，。！？；：、）」』])", r"\1", text)
        text = re.sub(r"([「『（])\s+", r"\1", text)
        return text

    def _normalize_quotes(self, text: str) -> str:
        text = re.sub(r'"([^"\n]{1,500})"', r'「\1」', text)
        text = re.sub(r"'([^'\n]{1,500})'", r"「\1」", text)
        return text

    def _normalize_paragraphs(self, text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"\n[ \t　]+\n", "\n\n", text)
        lines = [line.strip() for line in text.split("\n")]
        return "\n".join(lines).strip()

    def _paragraphs(self, text: str) -> List[str]:
        text = self._normalize_newlines(text).strip()
        return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    def _restore_source_paragraph_shape(self, source: str, translated: str) -> str:
        source_paras = self._paragraphs(source)
        out_paras = self._paragraphs(translated)

        # If the model already produced paragraph breaks, keep them.
        if len(out_paras) >= 2:
            return "\n\n".join(out_paras)

        # If source has multiple paragraphs but translation collapsed to one block,
        # split the translation into roughly the same number of paragraph blocks.
        if len(source_paras) <= 1 or len(out_paras) != 1:
            return translated

        single = out_paras[0]
        sentences = self._split_sentences(single)
        if len(sentences) <= len(source_paras):
            return translated

        weights = [max(1, len(p)) for p in source_paras]
        total = sum(weights)
        total_sent = len(sentences)

        groups: List[List[str]] = []
        cursor = 0
        for i, w in enumerate(weights):
            if i == len(weights) - 1:
                groups.append(sentences[cursor:])
                break
            take = max(1, round(total_sent * w / total))
            remaining_groups = len(weights) - i - 1
            max_take = max(1, len(sentences) - cursor - remaining_groups)
            take = min(take, max_take)
            groups.append(sentences[cursor:cursor + take])
            cursor += take

        rebuilt = ["".join(g).strip() for g in groups if g]
        return "\n\n".join(rebuilt)

    def _split_sentences(self, text: str) -> List[str]:
        # Keep punctuation with each sentence.
        parts = re.findall(r".+?[。！？](?:」)?|.+$", text)
        return [p.strip() for p in parts if p.strip()]

    def _split_overlong_paragraphs(self, text: str) -> str:
        paras = self._paragraphs(text)
        result: List[str] = []
        for para in paras:
            if len(para) <= 520:
                result.append(para)
                continue

            sentences = self._split_sentences(para)
            buf = ""
            for s in sentences:
                # Prefer Step002-style medium paragraphs, not one sentence per line.
                if len(buf) + len(s) <= 420:
                    buf += s
                else:
                    if buf.strip():
                        result.append(buf.strip())
                    buf = s
            if buf.strip():
                result.append(buf.strip())

        return "\n\n".join(result)


_default_formatter = FormatEngine()


def format_chunk(text: str, source: Optional[str] = None) -> str:
    return _default_formatter.format_chunk(text, source=source)


def format_document(parts: Iterable[str]) -> str:
    return _default_formatter.format_document(parts)
