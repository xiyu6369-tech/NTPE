from __future__ import annotations

from core.character_memory_v2 import FactType


NATURALNESS_POLICY = """【自然度政策（TE v7.2）】
- 忠實、完整、語意保存、術語一致與含混性保存優先於流暢度。
- 使用自然的繁體中文小說語序；對話使用「」；依時代、地區、敘事風格與人物口吻選詞，不強制台灣特有詞。
- 可調整韓文直譯語序、重複主詞、不自然連接詞與長定語結構，但不得摘要、刪減、增寫、補足因果或解釋未明示資訊。
- 不得改變否定、數字或時間；原文未出現全名時不得自動補全全名。"""


_FACT_LABELS = {
    FactType.CANONICAL_NAME: "人物固定譯名",
    FactType.NAME_VARIANT: "人物稱呼／別名",
    FactType.RELATIONSHIP: "人物關係",
    FactType.ADDRESSING_STYLE: "人物稱呼方式",
    FactType.SPEECH_STYLE: "人物語氣提示",
    FactType.ROLE_OR_IDENTITY: "人物身份提示",
}


def render_character_section(items: tuple[object, ...]) -> str:
    if not items:
        return ""
    lines = ["【人物一致性記憶（只作翻譯輔助，來源文字優先）】"]
    for item in items:
        label = _FACT_LABELS.get(item.fact_type, "人物一致性提示")
        lines.append(f"- {item.character_id}｜{label}：{item.value}｜來源可信度：已通過資格檢核")
    lines.append("- 不得利用記憶補寫來源未明示的資訊或補全未出現的全名。")
    return "\n".join(lines)


def render_context_section(items: tuple[object, ...]) -> str:
    if not items:
        return ""
    lines = ["【有限上下文連貫提示（不得摘要或改寫來源）】"]
    lines.extend(f"- {item.item_type}：{item.value}" for item in items)
    return "\n".join(lines)


def render_scene_section(items: tuple[object, ...]) -> str:
    if not items:
        return ""
    lines = ["【目前場景提示】"]
    lines.extend(f"- {item.item_type}：{item.value}" for item in items)
    return "\n".join(lines)


def render_quality_sections(*, characters: tuple[object, ...], contexts: tuple[object, ...], scenes: tuple[object, ...], naturalness: bool) -> str:
    sections = [
        render_character_section(characters),
        render_scene_section(scenes),
        render_context_section(contexts),
        NATURALNESS_POLICY if naturalness else "",
    ]
    return "\n".join(section for section in sections if section)

