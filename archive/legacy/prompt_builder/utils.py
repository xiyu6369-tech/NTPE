from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from datetime import datetime


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def load_json(path: str | Path) -> dict:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: str | Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    cjk = len(re.findall(r"[\u4e00-\u9fff\uac00-\ud7af\u3040-\u30ff]", text))
    other = max(len(text) - cjk, 0)
    return int(cjk + other / 4) + 1


def regex_search(pattern: str, text: str) -> bool:
    try:
        return re.search(pattern, text) is not None
    except re.error:
        return False
