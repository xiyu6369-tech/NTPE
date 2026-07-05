from __future__ import annotations

from pathlib import Path

from core.translation_engine.utils import save_json, save_text


def write_text_output(path: str | Path, text: str) -> Path:
    path = Path(path)
    save_text(path, text)
    return path


def write_json_output(path: str | Path, payload: dict) -> Path:
    path = Path(path)
    save_json(path, payload)
    return path
