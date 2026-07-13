from __future__ import annotations

import re

from .budget import estimate_tokens


def preserve_dialogue(text: str, token_budget: int) -> str:
    value = str(text or "")
    if estimate_tokens(value) <= token_budget:
        return value
    lines = value.splitlines()
    dialogue = [line for line in lines if _is_dialogue(line)]
    chosen: list[str] = []
    for line in reversed(dialogue):
        candidate = "\n".join(reversed([line, *chosen]))
        if estimate_tokens(candidate) > token_budget:
            continue
        chosen.insert(0, line)
    return "\n".join(chosen)


def _is_dialogue(line: str) -> bool:
    stripped = line.strip()
    return bool(re.match(r'^(?:[-—]|["“「『])', stripped) or re.search(r'["”」』]$', stripped))
