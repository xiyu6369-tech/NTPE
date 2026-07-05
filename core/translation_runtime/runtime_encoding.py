from __future__ import annotations

from pathlib import Path


def normalize_text(text: str) -> str:
    text = (text or "").replace("\ufeff", "").replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip() + "\n" if text.strip() else ""


def read_text_auto(path: str | Path) -> str:
    path = Path(path)
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr", "big5", "cp950"):
        try:
            return normalize_text(raw.decode(enc))
        except UnicodeDecodeError:
            continue
    return normalize_text(raw.decode("utf-8", errors="replace"))
