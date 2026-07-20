from __future__ import annotations

import re
import unicodedata


HANGUL_RE = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]")
LATIN_RE = re.compile(r"[A-Za-z]")
HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def normalize_source_name(value: str) -> str:
    return unicodedata.normalize("NFC", " ".join(value.strip().split())).casefold()


def contains_hangul(value: str) -> bool:
    return bool(HANGUL_RE.search(value))


def contains_latin(value: str) -> bool:
    return bool(LATIN_RE.search(value))


def contains_han(value: str) -> bool:
    return bool(HAN_RE.search(value))


def script_profile(value: str) -> dict[str, bool]:
    return {"hangul": contains_hangul(value), "latin": contains_latin(value), "han": contains_han(value)}


def is_valid_zh_hant_name_shape(value: str) -> bool:
    stripped = value.strip()
    if not stripped or contains_hangul(stripped) or contains_latin(stripped):
        return False
    significant = re.sub(r"[\s·・．.－—-]", "", stripped)
    return 1 < len(significant) <= 12 and bool(significant) and all(contains_han(char) for char in significant)
