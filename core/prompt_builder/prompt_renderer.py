from __future__ import annotations


class PromptRenderer:
    def render(
        self,
        *,
        profile: dict,
        chunk_text: str,
        character_matches: list[dict],
        glossary_matches: list[dict],
        rules: dict,
        context: dict,
        semantic_matches: list[dict] | None = None,
        document_structure: dict | None = None,
    ) -> dict:
        semantic_matches = semantic_matches or []
        document_structure = document_structure or {}

        target = profile.get("language", {}).get("target_variant", "Taiwan Traditional Chinese")
        system_prompt = (
            "你是 NTPE 的專業韓文小說翻譯引擎。"
            f"你的任務是將原文完整翻譯成{target}。"
            "你必須忠實保留原文資訊、敘事節奏、段落結構、人物語氣與小說畫面感。"
            "你必須遵守提供的人名、術語、語義鎖定與文件結構規則。"
            "只輸出譯文，不要加解釋。"
        )

        parts = []
        parts.append("【翻譯規則】")
        for group in ["global_rules", "character_rules", "semantic_rules", "format_rules", "negative_rules"]:
            for rule in rules.get(group, []):
                parts.append(f"- {rule}")

        if document_structure.get("has_title") and document_structure.get("title"):
            title = document_structure["title"]
            parts.append("")
            parts.append("【文件結構】")
            parts.append(f"- 第一行是標題，不是正文：{title.get('source', '')} → {title.get('target', '')}")
            parts.append("- 標題必須獨立輸出，不可接到正文第一句。")
            parts.append("- 標題後請保留空行，再開始正文。")

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

        if semantic_matches:
            parts.append("")
            parts.append("【本段語義鎖定】")
            for item in semantic_matches:
                preferred = item.get("preferred", "")
                required = item.get("required", [])
                forbidden = item.get("forbidden", [])
                note = item.get("note", "")

                if preferred:
                    parts.append(f"- {item['source']} → {preferred}")
                elif required:
                    parts.append(f"- {item['source']} 必須包含：{'／'.join(required)}")

                if forbidden:
                    parts.append(f"  禁止譯成：{'／'.join(forbidden)}")
                if note:
                    parts.append(f"  語義說明：{note}")

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
            "user_prompt": "\n".join(parts),
            "prompt_mode": "translate",
        }
