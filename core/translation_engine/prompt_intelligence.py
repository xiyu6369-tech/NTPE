from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Literal


TextProfile = Literal["literary", "dialogue_heavy", "narration_heavy", "formal", "general"]

PROMPT_INTELLIGENCE_VERSION = "3.0-stage01"
PROMPT_INTELLIGENCE_MARKER = "[NTPE Translation Engine v3.0 Prompt Intelligence]"

_DIALOGUE_MARKS = ("「", "」", "“", "”", '"', "'", "『", "』")
_FORMAL_MARKERS = (
    "therefore",
    "however",
    "nevertheless",
    "whereas",
    "hereby",
    "shall",
    "regarding",
    "pursuant",
    "합니다",
    "하십시오",
    "습니다",
    "존재",
    "하여",
)
_LITERARY_MARKERS = (
    "moon",
    "shadow",
    "silence",
    "breath",
    "heart",
    "dream",
    "wind",
    "night",
    "눈빛",
    "심장",
    "숨결",
    "어둠",
    "달빛",
    "침묵",
    "바람",
)


def detect_text_profile(text: str) -> TextProfile:
    """Detect the dominant prompt profile for a novel source chunk."""
    value = str(text or "").strip()
    if not value:
        return "general"

    lines = [line.strip() for line in value.splitlines() if line.strip()]
    dialogue_lines = sum(1 for line in lines if _looks_like_dialogue(line))
    dialogue_marks = sum(value.count(mark) for mark in _DIALOGUE_MARKS)
    sentence_count = max(1, len(re.findall(r"[.!?。！？]", value)) + value.count("\n"))
    dialogue_ratio = dialogue_lines / max(1, len(lines))

    lowered = value.lower()
    formal_hits = sum(1 for marker in _FORMAL_MARKERS if marker in lowered or marker in value)
    literary_hits = sum(1 for marker in _LITERARY_MARKERS if marker in lowered or marker in value)
    average_line_length = len(value) / max(1, len(lines))

    if dialogue_ratio >= 0.35 or dialogue_marks >= max(2, sentence_count // 3):
        return "dialogue_heavy"
    if formal_hits >= 2 and dialogue_ratio < 0.25:
        return "formal"
    if literary_hits >= 2 or (average_line_length >= 90 and sentence_count >= 3):
        return "literary"
    if len(lines) >= 3 and dialogue_ratio <= 0.15 and average_line_length >= 45:
        return "narration_heavy"
    return "general"


def build_quality_directives(profile: TextProfile | str) -> list[str]:
    """Build profile-aware Traditional Chinese novel translation directives."""
    normalized = _normalize_profile(profile)
    directives = [
        "Translate the full source text into Traditional Chinese; do not summarize, omit, merge, or add scenes.",
        "Use fluent Traditional Chinese suitable for novels, preserving the source's register and emotional pacing.",
        "Render dialogue with Traditional Chinese corner quotes 「」 and keep speaker intent clear.",
        "Maintain character voice, relationship distance, honorific nuance, and narrative point of view consistently.",
        "Avoid forced Taiwanese colloquial wording; use it only when the source tone naturally supports it.",
    ]

    profile_directives = {
        "dialogue_heavy": [
            "Prioritize natural spoken rhythm while preserving each character's distinct voice.",
            "Keep dialogue lines complete and avoid converting speech into narration.",
        ],
        "narration_heavy": [
            "Prioritize coherent narrative flow, scene continuity, and descriptive atmosphere.",
            "Keep exposition readable without flattening imagery or emotional subtext.",
        ],
        "formal": [
            "Preserve formal, archaic, ceremonial, or restrained diction when present in the source.",
            "Do not modernize formal speech into casual phrasing unless the source shifts register.",
        ],
        "literary": [
            "Preserve literary imagery, cadence, restraint, and implied emotion without over-explaining.",
            "Use polished novel prose rather than literal sentence-by-sentence stiffness.",
        ],
        "general": [
            "Balance accuracy, readability, and novel-like flow without changing the source meaning.",
        ],
    }
    return directives + profile_directives[normalized]


def enhance_prompt_package(package: dict[str, Any]) -> dict[str, Any]:
    """Return a v3.0-enhanced package without requiring a new package schema."""
    enhanced = deepcopy(package)
    if not isinstance(enhanced, dict):
        return enhanced

    source_text = _source_text_from_package(enhanced)
    profile = detect_text_profile(source_text)
    directives = build_quality_directives(profile)
    _attach_prompt_intelligence(enhanced, profile, directives)
    return enhanced


def apply_prompt_intelligence(package: dict[str, Any], source_text: str) -> dict[str, Any]:
    """Apply Prompt Intelligence with source text supplied by engine or runtime."""
    enhanced = deepcopy(package)
    if not isinstance(enhanced, dict):
        return enhanced

    profile = detect_text_profile(source_text or _source_text_from_package(enhanced))
    directives = build_quality_directives(profile)
    _attach_prompt_intelligence(enhanced, profile, directives)
    return enhanced


def _attach_prompt_intelligence(package: dict[str, Any], profile: TextProfile, directives: list[str]) -> None:
    prompt = package.setdefault("prompt", {})
    if not isinstance(prompt, dict):
        return

    metadata = package.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        package["metadata"] = metadata

    intelligence = {
        "version": PROMPT_INTELLIGENCE_VERSION,
        "profile": profile,
        "directives": directives,
    }
    metadata["prompt_intelligence"] = intelligence
    prompt["prompt_intelligence"] = intelligence
    prompt["quality_directives"] = directives

    user_prompt = str(prompt.get("user_prompt", ""))
    prompt["user_prompt"] = _inject_directives(user_prompt, directives, profile)


def _inject_directives(user_prompt: str, directives: list[str], profile: TextProfile) -> str:
    if PROMPT_INTELLIGENCE_MARKER in user_prompt:
        return user_prompt

    directive_block = "\n".join(f"- {directive}" for directive in directives)
    block = (
        f"{PROMPT_INTELLIGENCE_MARKER}\n"
        f"profile: {profile}\n"
        f"{directive_block}\n"
        "[/NTPE Translation Engine v3.0 Prompt Intelligence]\n"
    )
    return f"{block}\n{user_prompt}".strip() + ("\n" if user_prompt.endswith("\n") else "")


def _source_text_from_package(package: dict[str, Any]) -> str:
    source = package.get("source", {})
    if isinstance(source, dict):
        for key in ("chunk_text", "text", "source_text"):
            value = source.get(key)
            if isinstance(value, str):
                return value
    return ""


def _looks_like_dialogue(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if any(mark in stripped for mark in _DIALOGUE_MARKS):
        return True
    return bool(re.match(r"^[-–—]\s*\S+", stripped))


def _normalize_profile(profile: TextProfile | str) -> TextProfile:
    value = str(profile or "general").strip().lower()
    if value in {"literary", "dialogue_heavy", "narration_heavy", "formal", "general"}:
        return value  # type: ignore[return-value]
    return "general"
