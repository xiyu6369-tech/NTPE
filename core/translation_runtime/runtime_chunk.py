from __future__ import annotations

import re

DEFAULT_CHUNK_SIZE = 1800


def split_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> list[str]:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []
    if chunk_size < 300:
        raise ValueError("chunk_size must be >= 300")

    paragraphs = re.split(r"(\n{2,})", text + "\n")
    blocks: list[str] = []
    current = ""
    for item in paragraphs:
        if not item:
            continue
        candidate = current + item
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current.strip():
            blocks.extend(_split_oversized(current, chunk_size))
        current = item
    if current.strip():
        blocks.extend(_split_oversized(current, chunk_size))
    return [block.strip() + "\n" for block in blocks if block.strip()]


def _split_oversized(text: str, chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind("。"), window.rfind("！"), window.rfind("？"), window.rfind("."), window.rfind("\n"))
            if cut > chunk_size * 0.45:
                end = start + cut + 1
        pieces.append(text[start:end])
        start = end
    return pieces
