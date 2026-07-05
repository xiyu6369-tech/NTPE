from __future__ import annotations

import re

TAIWAN_TRADITIONAL_REPLACEMENTS = {
    "台湾": "台灣", "台北": "臺北", "里面": "裡面", "里头": "裡頭",
    "这里": "這裡", "那里": "那裡", "哪里": "哪裡", "为": "為",
    "这": "這", "个": "個", "后": "後", "说": "說", "还": "還",
    "会": "會", "对": "對", "发": "發", "头": "頭", "么": "麼",
    "没": "沒", "让": "讓", "过": "過", "时": "時", "间": "間",
    "门": "門", "声": "聲", "来": "來", "见": "見", "现": "現",
    "长": "長", "体": "體", "书": "書", "气": "氣", "脸": "臉",
    "边": "邊", "从": "從", "点": "點", "样": "樣", "听": "聽",
    "话": "話", "轻": "輕", "动": "動", "实": "實", "觉": "覺",
    "该": "該", "着": "著",
}


def clean_provider_output(text: str) -> str:
    result = text or ""
    for pattern in (r"^以下(?:是|為).{0,20}翻譯[:：]\s*", r"^譯文[:：]\s*", r"^翻譯結果[:：]\s*"):
        result = re.sub(pattern, "", result.strip(), flags=re.IGNORECASE)
    result = result.replace("\ufeff", "").replace("\x00", "")
    result = result.replace("\r\n", "\n").replace("\r", "\n")
    result = re.sub(r"[ \t]+\n", "\n", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def normalize_punctuation_for_zh_tw(text: str) -> str:
    result = text or ""
    result = result.replace("...", "……")
    result = result.replace(",", "，").replace(":", "：").replace(";", "；")
    result = result.replace("?", "？").replace("!", "！")
    result = result.replace("(", "（").replace(")", "）")
    result = re.sub(r'"([^"\n]{1,200})"', r"「\1」", result)
    result = re.sub(r"'([^'\n]{1,200})'", r"『\1』", result)
    result = re.sub(r"。{2,}", "。", result)
    result = re.sub(r"，{2,}", "，", result)
    result = re.sub(r"！{2,}", "！", result)
    result = re.sub(r"？{2,}", "？", result)
    return result


def normalize_taiwan_traditional(text: str) -> str:
    result = text or ""
    for simplified, traditional in sorted(TAIWAN_TRADITIONAL_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        result = result.replace(simplified, traditional)
    return result


def format_translation_output(text: str, *, enabled: bool = True, taiwan_traditional_normalization: bool = True) -> str:
    result = clean_provider_output(text)
    if not enabled:
        return result.strip()
    result = normalize_punctuation_for_zh_tw(result)
    if taiwan_traditional_normalization:
        result = normalize_taiwan_traditional(result)
    return clean_provider_output(result).strip()
