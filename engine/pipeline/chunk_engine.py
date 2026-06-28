from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    index: int
    text: str
    char_count: int
    start_paragraph: int
    end_paragraph: int

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "text": self.text,
            "char_count": self.char_count,
            "start_paragraph": self.start_paragraph,
            "end_paragraph": self.end_paragraph,
        }


class ChunkEngine:
    """
    NTPE v0.9.0 Chunk Engine

    目標：
    - 依段落切分。
    - 儘量接近 chunk_size。
    - 不在段落中間硬切，除非段落本身超過 max_chunk_size。
    """

    def __init__(self, chunk_size: int = 3000, max_chunk_size: int = 4200):
        self.chunk_size = int(chunk_size)
        self.max_chunk_size = int(max_chunk_size)

    def split(self, text: str) -> list[Chunk]:
        paragraphs = self._split_paragraphs(text)

        chunks: list[Chunk] = []
        current: list[str] = []
        current_len = 0
        start_para = 1

        for i, para in enumerate(paragraphs, start=1):
            para_len = len(para)

            if para_len > self.max_chunk_size:
                if current:
                    chunks.append(self._make_chunk(len(chunks) + 1, current, start_para, i - 1))
                    current = []
                    current_len = 0

                hard_parts = self._hard_split(para)
                for part in hard_parts:
                    chunks.append(Chunk(
                        index=len(chunks) + 1,
                        text=part.strip() + "\n",
                        char_count=len(part.strip()),
                        start_paragraph=i,
                        end_paragraph=i,
                    ))
                start_para = i + 1
                continue

            if current and current_len + para_len > self.chunk_size:
                chunks.append(self._make_chunk(len(chunks) + 1, current, start_para, i - 1))
                current = [para]
                current_len = para_len
                start_para = i
            else:
                if not current:
                    start_para = i
                current.append(para)
                current_len += para_len

        if current:
            chunks.append(self._make_chunk(len(chunks) + 1, current, start_para, len(paragraphs)))

        return chunks

    def _split_paragraphs(self, text: str) -> list[str]:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        parts = re.split(r"\n\s*\n", text)
        return [p.strip() for p in parts if p.strip()]

    def _make_chunk(self, index: int, paragraphs: list[str], start_para: int, end_para: int) -> Chunk:
        text = "\n\n".join(paragraphs).strip() + "\n"
        return Chunk(
            index=index,
            text=text,
            char_count=len(text),
            start_paragraph=start_para,
            end_paragraph=end_para,
        )

    def _hard_split(self, text: str) -> list[str]:
        # 先嘗試用句號等標點切，仍過長才硬切。
        sentences = re.split(r"(?<=[。！？!?\.])\s+", text)
        parts = []
        current = ""

        for sentence in sentences:
            if len(current) + len(sentence) > self.chunk_size and current:
                parts.append(current)
                current = sentence
            else:
                current += ("\n" if current else "") + sentence

        if current:
            parts.append(current)

        final = []
        for part in parts:
            if len(part) <= self.max_chunk_size:
                final.append(part)
            else:
                for i in range(0, len(part), self.chunk_size):
                    final.append(part[i:i + self.chunk_size])

        return final
