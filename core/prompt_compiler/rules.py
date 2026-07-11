from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptDisciplineRule:
    code: str
    instruction: str
    category: str = "fidelity"
    enabled_by_default: bool = True


FOUNDATION_DISCIPLINE_RULES: tuple[PromptDisciplineRule, ...] = (
    PromptDisciplineRule("NO_ADDED_PLOT", "不得新增原文不存在的事件、設定或劇情。"),
    PromptDisciplineRule("NO_PREVIOUS_RESTATEMENT", "不得重述前文、上一段或本段已翻譯過的資訊。"),
    PromptDisciplineRule("NO_ADDED_TRANSITION", "不得為了銜接或流暢而自行增加過渡敘述。"),
    PromptDisciplineRule("NO_ADDED_PSYCHOLOGY", "不得自行補充原文未表達的人物心理、動機或判斷。"),
    PromptDisciplineRule("NO_SUMMARIZATION", "不得摘要、濃縮、概括或省略原文資訊。"),
    PromptDisciplineRule("PRESERVE_INFORMATION_ORDER", "保持資訊與事件出現順序，不任意前移、後置或重組。"),
    PromptDisciplineRule("PRESERVE_PARAGRAPH_INTENT", "保留段落功能與敘事推進；可依中文節奏調整，但不得造成內容重述或遺漏。"),
    PromptDisciplineRule("PREVIOUS_CONTEXT_ONLY", "僅翻譯【Korean】中的當前內容；【Previous】只供承接語境，不得翻譯或改寫進輸出。"),
)


def foundation_rule_codes() -> tuple[str, ...]:
    return tuple(rule.code for rule in FOUNDATION_DISCIPLINE_RULES)


def enabled_discipline_rules() -> tuple[PromptDisciplineRule, ...]:
    return tuple(rule for rule in FOUNDATION_DISCIPLINE_RULES if rule.enabled_by_default)


def render_discipline_block(rules: tuple[PromptDisciplineRule, ...] | None = None) -> str:
    selected = rules if rules is not None else enabled_discipline_rules()
    if not selected:
        return ""
    lines = ["【翻譯紀律】"]
    lines.extend(f"- {rule.instruction}" for rule in selected)
    return "\n".join(lines)
