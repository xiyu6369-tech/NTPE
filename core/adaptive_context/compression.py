from __future__ import annotations

import re

from .budget import estimate_tokens


def compress_narrative(text: str, token_budget: int) -> str:
    value = " ".join(str(text or "").split())
    if estimate_tokens(value) <= token_budget:
        return value
    sentences = [part.strip() for part in re.split(r"(?<=[\u3002\uff01\uff1f.!?])\s*", value) if part.strip()]
    chosen: list[str] = []
    for sentence in sentences:
        candidate = " ".join([*chosen, sentence])
        if estimate_tokens(candidate) > token_budget:
            break
        chosen.append(sentence)
    if chosen:
        return " ".join(chosen)
    return ""
