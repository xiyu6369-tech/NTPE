from __future__ import annotations

from pathlib import Path

from .literary_style import LiteraryStyleRulesEngine


class NarrativeIntelligenceEngine:
    """
    TQF-06.4.2 Narrative Intelligence Engine

    整合分析：
    - Literary Style
    - Emotion
    - Pacing
    - Inner Monologue
    - Dialogue Beat
    - Scene Flow
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.literary_style = LiteraryStyleRulesEngine(root)

    def analyze(self, text: str) -> dict:
        literary = self.literary_style.analyze(text)

        return {
            "literary": literary,
            "emotion": self._analyze_emotion(text),
            "pacing": self._analyze_pacing(text),
            "inner_monologue": self._analyze_inner_monologue(text),
            "dialogue_beat": self._analyze_dialogue_beat(text),
            "scene_flow": self._analyze_scene_flow(text),
        }

    def build_prompt_rules(self, analysis: dict) -> list[str]:
        rules = []

        rules.extend(
            self.literary_style.build_prompt_rules(
                analysis.get("literary", {})
            )
        )

        for section in [
            "emotion",
            "pacing",
            "inner_monologue",
            "dialogue_beat",
            "scene_flow",
        ]:
            data = analysis.get(section, {})
            instruction = data.get("instruction")
            if instruction:
                rules.append(instruction)

        return rules

    def _analyze_emotion(self, text: str) -> dict:
        if any(k in text for k in ["불길", "예감", "기분"]):
            return {
                "type": "unease",
                "instruction": "本段情緒基調是不祥與警戒，譯文需保留壓抑感，不可寫得輕鬆。",
            }

        if "우울" in text:
            return {
                "type": "gloom",
                "instruction": "本段情緒偏鬱悶，譯文需保留低沉感。",
            }

        if "난감" in text:
            return {
                "type": "awkward",
                "instruction": "本段含困擾與尷尬，譯文需保留人物的猶豫與為難。",
            }

        return {}

    def _analyze_pacing(self, text: str) -> dict:
        paragraph_count = len(
            [p for p in text.replace("\r\n", "\n").split("\n\n") if p.strip()]
        )

        if paragraph_count >= 3:
            return {
                "type": "segmented",
                "instruction": "原文以多段推進節奏，譯文不可壓成單一大段，需保留段落停頓。",
            }

        if "멈칫" in text or "잠시" in text:
            return {
                "type": "pause",
                "instruction": "本段包含停頓或短暫沉默，譯文需保留節奏上的停頓感。",
            }

        return {}

    def _analyze_inner_monologue(self, text: str) -> dict:
        if any(k in text for k in ["생각", "기분", "예감", "느낌"]):
            return {
                "type": "inner_monologue",
                "instruction": "本段含內心活動，譯文不可改成客觀說明，需保留人物主觀感受。",
            }

        return {}

    def _analyze_dialogue_beat(self, text: str) -> dict:
        if any(k in text for k in ["말했다", "물었다", "중얼거렸다", "웃었다", "노려보았다"]):
            return {
                "type": "dialogue_beat",
                "instruction": "本段含對話節拍，需保留說話前後的表情、動作、停頓與語氣。",
            }

        return {}

    def _analyze_scene_flow(self, text: str) -> dict:
        if any(k in text for k in ["현관", "계단", "문", "방", "소파", "식탁"]):
            return {
                "type": "scene_flow",
                "instruction": "本段含場景移動或空間描寫，譯文需保持人物位置與場景連續性。",
            }

        if any(k in text for k in ["비", "하늘", "소리", "군화", "초인종"]):
            return {
                "type": "atmosphere_flow",
                "instruction": "本段含聲音或環境氛圍，譯文需保留畫面與聽覺效果。",
            }

        return {}