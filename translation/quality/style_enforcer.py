from __future__ import annotations

from .contract import QualityComponent, QualityContext, QualityIssue, QualityResult

S2T = {
    "为": "為", "这": "這", "个": "個", "说": "說", "里": "裡", "后": "後", "国": "國", "会": "會", "来": "來", "对": "對", "时": "時", "过": "過", "还": "還", "让": "讓", "与": "與", "发": "發", "台": "臺",
}


class StyleEnforcer(QualityComponent):
    name = "style_enforcer"

    def run(self, context: QualityContext, result: QualityResult) -> QualityResult:
        text = result.text or context.translated_text or ""
        original = text
        for src, dst in S2T.items():
            text = text.replace(src, dst)
        text = text.replace('"', '「', 1) if text.count('"') >= 2 else text
        if text != original:
            result.text = text
            result.repairs.append("style_zh_tw_normalized")
            result.add_issue(QualityIssue("STYLE_NORMALIZED", "text normalized to zh-TW style", "info"))
        else:
            result.text = text
        return result
