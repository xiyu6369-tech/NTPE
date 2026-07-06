# =====================================================
# NTPE 1.2 Professional
# Stage-16.2 Narrative Intelligence
# =====================================================

from __future__ import annotations

import re
from typing import Iterable, List

from .narrative_result import NarrativeFinding, NarrativeSegment

FIRST_PERSON = ("我", "我們", "俺", "咱")
SECOND_PERSON = ("你", "你們", "您")
THIRD_PERSON = ("他", "她", "它", "他們", "她們", "這個人", "那個人")
PAST_MARKERS = ("曾", "已經", "之前", "當時", "那時", "過去")
PRESENT_MARKERS = ("現在", "此刻", "正在", "眼下")
EMOTION_KEYWORDS = {
    "tense": ("緊張", "害怕", "恐懼", "不安", "僵住", "顫抖"),
    "angry": ("憤怒", "生氣", "怒", "火大", "咬牙"),
    "sad": ("難過", "悲傷", "哭", "沉默", "失落"),
    "warm": ("微笑", "安心", "溫柔", "放鬆", "愉快"),
}
SCENE_MARKERS = ("隔天", "翌日", "幾天後", "同時", "另一邊", "回到", "場景", "夜裡", "清晨")


def split_segments(text: str) -> List[NarrativeSegment]:
    pieces = [line.strip() for line in re.split(r"\n+", text or "") if line.strip()]
    if not pieces and text and text.strip():
        pieces = [text.strip()]
    segments: List[NarrativeSegment] = []
    for index, piece in enumerate(pieces, start=1):
        kind = "dialogue" if piece.startswith(('「', '『', '"', '“')) or piece.endswith(('」', '』', '"', '”')) else "narration"
        segments.append(NarrativeSegment(segment_id=f"nar_{index}", text=piece, kind=kind))
    return segments


def detect_perspective(text: str) -> str:
    counts = {
        "first_person": sum(text.count(token) for token in FIRST_PERSON),
        "second_person": sum(text.count(token) for token in SECOND_PERSON),
        "third_person": sum(text.count(token) for token in THIRD_PERSON),
    }
    best, score = max(counts.items(), key=lambda item: item[1])
    return best if score > 0 else "unknown"


def detect_tense(text: str) -> str:
    past = sum(text.count(token) for token in PAST_MARKERS)
    present = sum(text.count(token) for token in PRESENT_MARKERS)
    if past > present:
        return "past"
    if present > past:
        return "present"
    return "undetermined"


def detect_emotional_tone(text: str) -> str:
    scores = {tone: sum(text.count(token) for token in tokens) for tone, tokens in EMOTION_KEYWORDS.items()}
    best, score = max(scores.items(), key=lambda item: item[1])
    return best if score > 0 else "neutral"


def detect_voice(segments: Iterable[NarrativeSegment]) -> str:
    materialized = list(segments)
    if not materialized:
        return "neutral"
    dialogue = sum(1 for segment in materialized if segment.kind == "dialogue")
    density = dialogue / max(len(materialized), 1)
    if density >= 0.65:
        return "dialogue_driven"
    if density <= 0.25:
        return "descriptive"
    return "balanced"


def detect_scene_transitions(segments: Iterable[NarrativeSegment]) -> List[str]:
    transitions: List[str] = []
    for segment in segments:
        if any(marker in segment.text for marker in SCENE_MARKERS):
            transitions.append(segment.segment_id)
    return transitions


def validate_narrative_consistency(segments: List[NarrativeSegment], perspective: str, tense: str) -> List[NarrativeFinding]:
    findings: List[NarrativeFinding] = []
    if not segments:
        findings.append(NarrativeFinding("narrative_input", "error", "No narrative segments were provided."))
    if perspective == "unknown":
        findings.append(NarrativeFinding("perspective", "warning", "Narrative perspective could not be determined."))
    if tense == "undetermined":
        findings.append(NarrativeFinding("tense", "info", "Narrative tense is not explicitly marked."))
    for segment in segments:
        if segment.kind == "dialogue" and not (segment.text.startswith(('「', '『', '"', '“')) and segment.text.endswith(('」', '』', '"', '”'))):
            findings.append(NarrativeFinding("dialogue_format", "warning", "Dialogue boundary may be incomplete.", segment.segment_id))
    return findings
