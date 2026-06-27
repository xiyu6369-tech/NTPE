import json
import re
from pathlib import Path
from typing import Dict, Tuple, List

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RULES_DIR = ROOT / "rules"

GLOSSARY_FILE = DATA_DIR / "glossary.txt"
TRANSLATION_RULES_FILE = RULES_DIR / "translation_rules.json"
HALLUCINATION_GUARD_FILE = RULES_DIR / "hallucination_guard.json"


DEFAULT_POST_REPLACE = {
    "寬松": "寬鬆",
    "裏": "裡",
    "爲": "為",
    "嘔了一口氣": "咂了咂嘴",
    "怒不可遜": "怒不可遏",
    "拉古恩": "潟湖",
    "酒店大堂": "飯店大廳",
}


DEFAULT_BAD_NAME_PATTERNS = {
    "正太義": "鄭泰義",
    "鄭太義": "鄭泰義",
    "鄭泰意": "鄭泰義",
    "卡爾": "凱爾",
}


DEFAULT_FORBIDDEN_AI_TEXT = [
    "很抱歉",
    "無法協助",
    "不能提供",
    "作為AI",
    "作為一個AI",
    "以下是翻譯",
    "翻譯如下",
]


DEFAULT_HALLUCINATION_PATTERNS = [
    "男人似乎是個種族主義者",
    "那個男人似乎是個種族主義者",
    "他是種族主義者",
    "對亞洲人有很深的偏見",
    "他的眼睛似乎能看透一切",
    "繼續自己的生活",
    "心情仍然很平靜和愉快",
    "沒有任何弱點",
    "很堅毅",
    "基於過去的經歷",
    "三天三夜",
]


def _load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        return default


def load_glossary() -> Dict[str, str]:
    """
    Read data/glossary.txt.

    Supported formats:
      정태의=鄭泰義
      정태의 -> 鄭泰義
    """
    glossary: Dict[str, str] = {}
    if not GLOSSARY_FILE.exists():
        return glossary

    with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue

            if "->" in raw:
                src, dst = raw.split("->", 1)
            elif "=" in raw:
                src, dst = raw.split("=", 1)
            else:
                continue

            src = src.strip()
            dst = dst.strip()
            if src and dst:
                glossary[src] = dst

    return glossary


def glossary_text(glossary: Dict[str, str]) -> str:
    if not glossary:
        return "（無）"

    # Long source terms first prevents partial-name ambiguity in the prompt.
    items = sorted(glossary.items(), key=lambda x: len(x[0]), reverse=True)
    return "\n".join(f"- {src} = {dst}" for src, dst in items)


def _load_post_rules() -> Dict[str, str]:
    data = _load_json(TRANSLATION_RULES_FILE, {})
    rules: Dict[str, str] = {}

    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(k, str) and isinstance(v, str):
                rules[k] = v
    elif isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            src = item.get("from") or item.get("source") or item.get("src")
            dst = item.get("to") or item.get("target") or item.get("dst")
            if isinstance(src, str) and isinstance(dst, str):
                rules[src] = dst

    merged = {}
    merged.update(DEFAULT_POST_REPLACE)
    merged.update(rules)
    return merged


def apply_postprocess(text: str) -> str:
    """
    Mechanical post-processing only.
    Do not add new meaning here.
    """
    if not text:
        return text

    fixed = text

    for src, dst in _load_post_rules().items():
        fixed = fixed.replace(src, dst)

    # Normalize quote style without touching apostrophes inside words.
    fixed = fixed.replace('"', "」")
    fixed = re.sub(r"」([^」]+)」", r"「\1」", fixed)

    # Remove common AI wrappers if they appear.
    fixed = re.sub(r"^\s*(以下是|以下為)?\s*翻譯[:：]\s*", "", fixed)
    fixed = fixed.strip()

    return fixed


def enforce_glossary_output(source: str, translated: str, glossary: Dict[str, str]) -> str:
    """
    Enforce known wrong name variants and obvious glossary output.
    This avoids relying only on the model.
    """
    fixed = translated

    for bad, good in DEFAULT_BAD_NAME_PATTERNS.items():
        fixed = fixed.replace(bad, good)

    for src, dst in sorted(glossary.items(), key=lambda x: len(x[0]), reverse=True):
        # If source term appears in Korean chunk, required Chinese term should appear.
        # We cannot safely insert missing terms, but we can normalize common variants.
        if src in source:
            if dst == "鄭泰義":
                fixed = fixed.replace("正太義", "鄭泰義").replace("鄭太義", "鄭泰義").replace("鄭泰意", "鄭泰義")
            if dst == "凱爾":
                fixed = fixed.replace("卡爾", "凱爾")

    return fixed


def _korean_count(text: str) -> int:
    return len(re.findall(r"[가-힣]", text or ""))


def _repeated_line_score(text: str) -> int:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 6:
        return 0
    return len(lines) - len(set(lines))


def _has_bad_name(text: str) -> List[str]:
    return [bad for bad in DEFAULT_BAD_NAME_PATTERNS if bad in text]


def _hallucination_patterns() -> List[str]:
    data = _load_json(HALLUCINATION_GUARD_FILE, DEFAULT_HALLUCINATION_PATTERNS)
    if isinstance(data, list):
        return [x for x in data if isinstance(x, str) and x.strip()]
    if isinstance(data, dict):
        raw = data.get("patterns", DEFAULT_HALLUCINATION_PATTERNS)
        if isinstance(raw, list):
            return [x for x in raw if isinstance(x, str) and x.strip()]
    return DEFAULT_HALLUCINATION_PATTERNS


def _has_hallucination_risk(source: str, translated: str) -> List[str]:
    """
    Conservative high-risk check.

    This does not try to understand the whole text.
    It blocks phrases we already observed as harmful additions in PASSION benchmark.
    """
    hits = []

    for phrase in _hallucination_patterns():
        if phrase in translated:
            hits.append(phrase)

    # Generic over-explanation markers.
    # Keep this narrow; broad blocking would cause too many false positives.
    risky_regexes = [
        r"他知道那個男人是個[^，。！？]*",
        r"那個男人是個種族主義者",
        r"這說明[^。！？]*",
        r"由此可見[^。！？]*",
    ]
    for pattern in risky_regexes:
        m = re.search(pattern, translated)
        if m:
            hits.append(m.group(0))

    return hits


def validate_translation(source: str, translated: str, glossary: Dict[str, str]) -> Tuple[bool, str]:
    """
    Return:
      (True, "OK")
      (False, reason)

    This function is intentionally strict about P0 issues:
    - empty output
    - AI refusal/wrapper
    - wrong required glossary names
    - Korean residue
    - severe summary/short output
    - repeated blocks
    - known hallucination patterns
    """
    src = source or ""
    dst = (translated or "").strip()

    if not dst:
        return False, "譯文為空"

    for phrase in DEFAULT_FORBIDDEN_AI_TEXT:
        if phrase in dst:
            return False, f"出現AI說明/拒答：{phrase}"

    bad_names = _has_bad_name(dst)
    if bad_names:
        return False, "出現錯誤譯名：" + ", ".join(bad_names)

    for src_term, dst_term in glossary.items():
        if src_term in src and dst_term and dst_term not in dst:
            return False, f"固定譯名缺失：{src_term} -> {dst_term}"

    korean_count = _korean_count(dst)
    if korean_count >= 10:
        return False, f"韓文殘留過多：{korean_count}"

    # Korean-to-Chinese length is not 1:1. Keep threshold practical.
    min_len = max(80, int(len(src) * 0.25))
    if len(dst) < min_len:
        return False, f"譯文過短，疑似摘要或漏翻：{len(dst)} < {min_len}"

    repeated = _repeated_line_score(dst)
    if repeated >= 3:
        return False, f"重複段落過多：{repeated}"

    risks = _has_hallucination_risk(src, dst)
    if risks:
        return False, "疑似新增推論內容：" + " / ".join(risks[:3])

    return True, "OK"
