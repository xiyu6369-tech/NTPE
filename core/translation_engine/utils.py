from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_json(path: str | Path) -> dict:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: str | Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_text(path: str | Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def append_log(path: str | Path, message: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = now_iso()
    with path.open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {message}\n")


def clean_translation_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("\x00", "")
    text = text.strip()
    return text + "\n" if text else ""
