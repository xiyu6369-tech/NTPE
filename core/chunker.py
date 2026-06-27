import re
from typing import List


def smart_chunk(text: str, max_size: int = 1800, min_size: int = 350) -> List[str]:
    """Scene/paragraph aware chunker for novels.

    Priority:
    1. Keep blank-line paragraphs intact.
    2. Avoid splitting dialogue from nearby narration when possible.
    3. Split oversized paragraphs by sentence punctuation.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []

    blocks = re.split(r"\n\s*\n", text)
    chunks: List[str] = []
    current = ""

    def flush():
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
            current = ""

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        if len(block) > max_size:
            flush()
            for part in split_long_block(block, max_size):
                chunks.append(part.strip())
            continue

        candidate = (current + "\n\n" + block).strip() if current else block
        if len(candidate) <= max_size:
            current = candidate
        else:
            if len(current) < min_size:
                current = candidate
            else:
                flush()
                current = block

    flush()
    return chunks


def split_long_block(block: str, max_size: int) -> List[str]:
    sentences = re.split(r"(?<=[。！？!?\.])\s+|(?<=[다요죠까네라])\s+", block)
    result: List[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_size:
            if current:
                result.append(current)
                current = ""
            for i in range(0, len(sentence), max_size):
                result.append(sentence[i:i + max_size])
            continue
        candidate = (current + " " + sentence).strip() if current else sentence
        if len(candidate) <= max_size:
            current = candidate
        else:
            if current:
                result.append(current)
            current = sentence
    if current:
        result.append(current)
    return result
