from __future__ import annotations


class ContextBuilder:
    def __init__(self, max_chars: int = 1800):
        self.max_chars = max_chars

    def build(self, states: dict, previous_tail: str = "") -> dict:
        story = states.get("story_state", {})
        character = states.get("character_state", {})
        scene = states.get("scene_state", {})
        dialogue = states.get("dialogue_state", {})
        narrative = states.get("narrative_state", {})

        lines = ["【NTPE Context Memory】"]

        if story:
            lines.append(f"- 目前檔案：{story.get('current_file', '')}")
            lines.append(f"- 目前 Chunk：{story.get('current_chunk', '')}")
            events = story.get("recent_events", [])[-5:]
            if events:
                lines.append("- 最近事件：")
                for item in events:
                    lines.append(f"  - {item.get('event', '')}")

        if scene:
            parts = []
            if scene.get("location"):
                parts.append(f"場景={scene['location']}")
            if scene.get("time"):
                parts.append(f"時間={scene['time']}")
            if scene.get("weather"):
                parts.append(f"天氣={scene['weather']}")
            if scene.get("mood"):
                parts.append(f"氣氛={scene['mood']}")
            if parts:
                lines.append("- 場景狀態：" + "；".join(parts))
            if scene.get("objects"):
                lines.append("- 場景物件：" + "、".join(scene.get("objects", [])[-8:]))

        if character:
            active = character.get("active_characters", [])
            if active:
                lines.append("- 目前活躍人物：" + "、".join(active))
            chars = character.get("characters", {})
            for name in active[-5:]:
                state = chars.get(name, {})
                desc = []
                if state.get("emotion"):
                    desc.append(f"情緒={state['emotion']}")
                if state.get("focus"):
                    desc.append(f"注意={state['focus']}")
                if state.get("notes"):
                    desc.append("補充=" + "；".join(state["notes"][-2:]))
                if desc:
                    lines.append(f"  - {name}：" + "；".join(desc))

        if dialogue:
            if dialogue.get("in_dialogue"):
                lines.append("- 目前處於對話場景。")
            recent = dialogue.get("recent_dialogue", [])[-4:]
            if recent:
                lines.append("- 最近對話：")
                for item in recent:
                    lines.append(f"  - {item.get('text', '')}")

        if narrative:
            if narrative.get("tone"):
                lines.append(f"- 敘事語氣：{narrative['tone']}")
            if narrative.get("narrative_focus"):
                lines.append("- 敘事重點：" + "、".join(narrative.get("narrative_focus", [])[-6:]))
            if narrative.get("emotion_flow"):
                lines.append("- 情緒流：" + " → ".join(narrative.get("emotion_flow", [])[-5:]))

        if previous_tail:
            lines.append("【上一段尾端】")
            lines.append(previous_tail[-500:])

        text = "\n".join(lines).strip()
        if len(text) > self.max_chars:
            text = text[-self.max_chars:]

        return {
            "previous_summary": text,
            "previous_chunk_tail": previous_tail[-500:] if previous_tail else "",
            "recent_characters": character.get("active_characters", [])[-8:] if character else [],
            "recent_terms": scene.get("objects", [])[-8:] if scene else [],
            "context_memory": states,
        }
