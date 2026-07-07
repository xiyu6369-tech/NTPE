from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NarrativeContext:
    perspective: str = "第三人稱小說敘事"
    scene_hints: list[str] = field(default_factory=list)
    mood_hints: list[str] = field(default_factory=list)
    lexical_hints: list[str] = field(default_factory=list)
    long_sentence_hints: list[str] = field(default_factory=list)

    @classmethod
    def analyze(cls, chunk_text: str, previous_context: str = "") -> "NarrativeContext":
        scene: list[str] = []
        mood: list[str] = []
        lexical: list[str] = []
        long_sentence: list[str] = []

        if any(token in chunk_text for token in ("호텔", "로비", "섬", "바닷가", "라군")):
            scene.append("場景可能包含酒店／大廳／島嶼／海邊等度假場域；用詞依作品背景自然選擇。")
        if "베를린" in chunk_text or "독일" in chunk_text:
            scene.append("故事含德國／柏林背景，譯文不需要刻意本地化。")
        if "난감" in chunk_text:
            mood.append("난감하다 應依語境處理為為難、傷腦筋、不知如何是好等心理狀態。")
        if "한숨" in chunk_text:
            mood.append("嘆息通常表示煩惱、無奈或放下心情，需結合上下文。")
        if "주장" in chunk_text:
            lexical.append("주장하다 在小說中常可譯為堅持說、主張、理直氣壯地表示，需確認主詞。")
        if "호텔" in chunk_text:
            lexical.append("호텔 可依背景譯為酒店、飯店或旅館；不要僵硬固定為單一地區用語。")

        # crude but useful: Korean long sentence / inserted phrase indication.
        for paragraph in chunk_text.splitlines():
            if paragraph.count(",") + paragraph.count("，") >= 3 or len(paragraph) > 220:
                long_sentence.append("本段有長句或插入語，翻譯時應先切分敘事單位，再保持主詞與行為者正確。")
                break

        return cls(scene_hints=scene, mood_hints=mood, lexical_hints=lexical, long_sentence_hints=long_sentence)

    def render(self) -> str:
        def block(title: str, items: list[str]) -> str:
            return f"【{title}】\n" + ("\n".join(f"- {x}" for x in items) if items else "- 依原文判斷")
        return "\n\n".join([
            f"【Narrative Perspective】\n- {self.perspective}",
            block("Scene Hints", self.scene_hints),
            block("Mood / Psychological Hints", self.mood_hints),
            block("Lexical Hints", self.lexical_hints),
            block("Long Sentence Hints", self.long_sentence_hints),
        ])

    def to_dict(self) -> dict:
        return {
            "perspective": self.perspective,
            "scene_hints": self.scene_hints,
            "mood_hints": self.mood_hints,
            "lexical_hints": self.lexical_hints,
            "long_sentence_hints": self.long_sentence_hints,
        }
