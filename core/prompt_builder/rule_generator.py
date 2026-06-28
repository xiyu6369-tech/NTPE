from __future__ import annotations


class RuleGenerator:
    def __init__(self, profile: dict):
        self.profile = profile

    def generate(self) -> dict:
        return {
            "global_rules": list(self.profile.get("translation_style", {}).get("requirements", [])),
            "character_rules": [
                "全名必須翻成全名。",
                "名字單獨出現時只翻名字，不可擴展成全名。",
                "姓氏單獨出現時只翻姓氏，不可擴展成全名。",
                "韓文無空格姓名視為完整姓名，不可拆分。",
                "必須遵守 Character Database 的 locked_dictionary。",
            ],
            "format_rules": [
                "對話使用「」。",
                "保留原文段落結構。",
                "不要輸出 Markdown 標題。",
                "不要加上「以下為翻譯」等說明文字。",
            ],
            "negative_rules": [
                "不可漏翻。",
                "不可摘要。",
                "不可改寫劇情。",
                "不可自行新增原文沒有的內容。",
                "不可留下大量韓文原文。",
                "不可把單獨名字翻成全名。",
            ],
        }
