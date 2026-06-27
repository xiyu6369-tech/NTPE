from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


SCENE_BREAK_PATTERNS = [
    r"^\s*[-―—]{3,}\s*$",
    r"^\s*[＊*]{3,}\s*$",
    r"^\s*[=＝]{3,}\s*$",
    r"^\s*[#＃]{3,}\s*$",
    r"^\s*第\s*\d+\s*[章話節].*$",
    r"^\s*\d+\s*$",
]


@dataclass
class ChunkOptions:
    target_size: int = 1100
    hard_limit: int = 1500
    min_size: int = 350


class ChunkEngine:
    """Scene / paragraph first chunker for long-form fiction.

    Goals:
    - Keep blank-line paragraphs intact whenever possible.
    - Avoid feeding the model very large semantic units.
    - Prefer splitting at scene markers and paragraph boundaries.
    - Split long paragraphs only as a last resort.
    """

    def __init__(self, options: ChunkOptions | None = None):
        self.options = options or ChunkOptions()

    def split(self, text: str) -> List[str]:
        text = self._normalize_newlines(text)
        blocks = self._split_blocks(text)
        chunks: List[str] = []
        current: List[str] = []
        current_len = 0

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # Scene separators should close the previous chunk.
            if self._is_scene_break(block) and current:
                chunks.append(self._join_blocks(current))
                current = [block]
                current_len = len(block)
                continue

            # Long single block: flush current, split safely.
            if len(block) > self.options.hard_limit:
                if current:
                    chunks.append(self._join_blocks(current))
                    current = []
                    current_len = 0
                chunks.extend(self._split_long_block(block))
                continue

            proposed_len = current_len + (2 if current else 0) + len(block)

            # Normal paragraph boundary split.
            if proposed_len > self.options.target_size and current_len >= self.options.min_size:
                chunks.append(self._join_blocks(current))
                current = [block]
                current_len = len(block)
            else:
                current.append(block)
                current_len = proposed_len

        if current:
            chunks.append(self._join_blocks(current))

        return [c.strip() for c in chunks if c.strip()]

    def _normalize_newlines(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Keep paragraph breaks, but remove excessive empty lines.
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _split_blocks(self, text: str) -> List[str]:
        # A block is separated by one or more blank lines.
        return re.split(r"\n\s*\n", text)

    def _join_blocks(self, blocks: List[str]) -> str:
        return "\n\n".join(b.strip() for b in blocks if b.strip())

    def _is_scene_break(self, block: str) -> bool:
        one_line = block.strip()
        return any(re.match(pattern, one_line) for pattern in SCENE_BREAK_PATTERNS)

    def _split_long_block(self, block: str) -> List[str]:
        # Split by sentence endings. Keep the delimiter with the sentence.
        sentences = re.split(
            r"(?<=[.!?。！？]|다\.|요\.|까\.|죠\.|네\.|다|요|까|죠|네)\s+",
            block.strip(),
        )
        chunks: List[str] = []
        buf: List[str] = []
        buf_len = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Extremely long sentence fallback: hard slice, but this should be rare.
            if len(sentence) > self.options.hard_limit:
                if buf:
                    chunks.append(" ".join(buf).strip())
                    buf = []
                    buf_len = 0
                chunks.extend(self._hard_slice(sentence))
                continue

            proposed = buf_len + (1 if buf else 0) + len(sentence)
            if proposed > self.options.target_size and buf:
                chunks.append(" ".join(buf).strip())
                buf = [sentence]
                buf_len = len(sentence)
            else:
                buf.append(sentence)
                buf_len = proposed

        if buf:
            chunks.append(" ".join(buf).strip())
        return chunks

    def _hard_slice(self, text: str) -> List[str]:
        limit = self.options.hard_limit
        return [text[i:i + limit].strip() for i in range(0, len(text), limit) if text[i:i + limit].strip()]


def split_chunks(text: str, size: int = 1100) -> List[str]:
    options = ChunkOptions(target_size=size, hard_limit=max(size + 400, 1400))
    return ChunkEngine(options).split(text)
