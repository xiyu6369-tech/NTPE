import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "rules"
DATA_DIR = ROOT / "data"


def _load_json(path: Path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_translation_rules():
    return _load_json(RULES_DIR / "translation_rules.json", {})


def load_forbidden_phrases():
    return _load_json(RULES_DIR / "forbidden_phrases.json", [])


def load_glossary():
    glossary = {}
    path = DATA_DIR / "glossary.txt"
    if not path.exists():
        return glossary
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            src, dst = line.split("=", 1)
        elif "->" in line:
            src, dst = line.split("->", 1)
        else:
            continue
        src = src.strip()
        dst = dst.strip()
        if src and dst:
            glossary[src] = dst
    return glossary


def glossary_text(glossary: dict) -> str:
    if not glossary:
        return "（無）"
    items = sorted(glossary.items(), key=lambda x: len(x[0]), reverse=True)
    return "\n".join(f"- {src} = {dst}" for src, dst in items)


def apply_postprocess(text: str) -> str:
    rules = load_translation_rules()
    # Longer source first to avoid partial replacement issues.
    for wrong, right in sorted(rules.items(), key=lambda x: len(x[0]), reverse=True):
        text = text.replace(wrong, right)
    return text


def enforce_glossary_output(src_text: str, zh_text: str, glossary: dict) -> str:
    """Make obvious wrong variants converge to glossary terms.

    This is intentionally conservative: it only fixes configured aliases and does
    not attempt to guess new names.
    """
    aliases = {
        "正太義": "鄭泰義",
        "鄭太義": "鄭泰義",
        "鄭泰意": "鄭泰義",
        "卡爾": "凱爾",
        "凱爾・里格羅": "凱爾・里格勞",
        "伊萊・里格羅": "伊萊・里格勞",
    }
    for bad, good in aliases.items():
        zh_text = zh_text.replace(bad, good)
    return zh_text


def contains_korean(text: str) -> bool:
    return bool(re.search(r"[가-힣]", text))


def repeated_lines(text: str) -> bool:
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    if len(lines) < 6:
        return False
    return len(lines) - len(set(lines)) >= 3


def validate_translation(src_text: str, zh_text: str, glossary: dict):
    """Return (ok, reason)."""
    if not zh_text or not zh_text.strip():
        return False, "空白譯文"

    bad_markers = ["很抱歉", "無法協助", "不能提供", "我不能", "作為AI"]
    if any(x in zh_text for x in bad_markers):
        return False, "AI拒答或說明文字"

    if contains_korean(zh_text):
        korean_count = len(re.findall(r"[가-힣]", zh_text))
        if korean_count >= 10:
            return False, "韓文殘留過多"

    if repeated_lines(zh_text):
        return False, "重複段落"

    # Avoid heavy compression. Korean to Chinese length can vary a lot, so keep this loose.
    if len(zh_text) < max(80, len(src_text) * 0.18):
        return False, "譯文過短，疑似摘要或漏翻"

    forbidden = load_forbidden_phrases()
    for phrase in forbidden:
        if phrase and phrase in zh_text:
            return False, f"出現禁止推論詞：{phrase}"

    # Glossary regression checks: if source contains Korean name, output must contain configured Chinese name.
    for src, dst in glossary.items():
        if src in src_text and dst not in zh_text:
            return False, f"固定譯名缺失：{src} -> {dst}"

    return True, "OK"
