from __future__ import annotations


class PromptRenderer:
    def render(self, *, profile: dict, chunk_text: str, character_matches: list[dict], glossary_matches: list[dict], rules: dict, context: dict) -> dict:
        target = profile.get("language", {}).get("target_variant", "Taiwan Traditional Chinese")
        system_prompt = (
            "你是 NTPE 的專業小說翻譯引擎。"
            f"你的任務是將原文完整翻譯成{target}。"
            "你必須遵守提供的人名、術語與格式規則。"
            "只輸出譯文，不要加解釋。"
        )

        parts = []
        parts.append("【翻譯規則】")
        for group in ["global_rules", "character_rules", "format_rules", "negative_rules"]:
            for rule in rules.get(group, []):
                parts.append(f"- {rule}")

        if character_matches:
            parts.append("")
            parts.append("【本段人物譯名】")
            for item in character_matches:
                parts.append(f"- {item['source']} → {item['target']}（{item.get('rule', '')}）")

        if glossary_matches:
            parts.append("")
            parts.append("【本段術語】")
            for item in glossary_matches:
                if item.get("target"):
                    parts.append(f"- {item['source']} → {item['target']}")
                else:
                    parts.append(f"- {item['source']}")

        if context.get("previous_summary") or context.get("previous_chunk_tail"):
            parts.append("")
            parts.append("【前文參考】")
            if context.get("previous_summary"):
                parts.append(context["previous_summary"])
            if context.get("previous_chunk_tail"):
                parts.append(context["previous_chunk_tail"])

        parts.append("")
        parts.append("【待翻譯內容】")
        parts.append(chunk_text)

        return {
            "system_prompt": system_prompt,
            "user_prompt": "\\n".join(parts),
            "prompt_mode": "translate",
        }
