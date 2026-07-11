from __future__ import annotations

from dataclasses import dataclass

NATURALNESS_POLICY_VERSION = "6.0.0-stage12.4"


@dataclass(frozen=True)
class NaturalnessRule:
    code: str
    instruction: str
    category: str


NATURALNESS_RULES: tuple[NaturalnessRule, ...] = (
    NaturalnessRule(
        "NATURAL_CHINESE_SYNTAX",
        "依繁體中文小說語序自然重組句子，避免保留韓文或外語的生硬修飾順序與機械句型。",
        "naturalness",
    ),
    NaturalnessRule(
        "ERA_APPROPRIATE_WORDING",
        "依作品時代、地域與人物身分選詞；不強制使用台灣特有用語，也不得使用不合背景的現代口語。",
        "style",
    ),
    NaturalnessRule(
        "NO_UNSUPPORTED_SPECIFICITY",
        "不得把原文含糊資訊具體化，不得自行新增地名、交通方式、時間長度、動作強度或背景設定。",
        "fidelity",
    ),
    NaturalnessRule(
        "PRESERVE_CHARACTER_VOICE",
        "保持同一角色在相同情境中的稱呼、敬語層級與口吻一致；不得自行放大人物情緒或改變角色性格；保持原文敘事人稱、視角與敘事距離。",
        "characterization",
    ),
)


def render_naturalness_policy(rules: tuple[NaturalnessRule, ...] | None = None) -> str:
    selected = rules if rules is not None else NATURALNESS_RULES
    if not selected:
        return ""
    lines = ["【小說語感規範】"]
    lines.extend(f"- {rule.instruction}" for rule in selected)
    return "\n".join(lines)
