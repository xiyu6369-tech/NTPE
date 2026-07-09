from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Literal


ContextProfile = Literal["dialogue_heavy", "narration_heavy", "descriptive", "tension", "neutral"]

CONTEXT_INTELLIGENCE_VERSION = "3.0-stage02"
CONTEXT_INTELLIGENCE_MARKER = "[NTPE Translation Engine v3.0 Context Intelligence]"

_DIALOGUE_MARKS = ("「", "」", "“", "”", '"', "'", "『", "』")
_TENSION_MARKERS = (
    "gasp",
    "shiver",
    "tremble",
    "fear",
    "panic",
    "blood",
    "breath",
    "dark",
    "倒抽",
    "悶哼",
    "顫",
    "恐懼",
    "緊張",
    "血",
    "숨",
    "떨",
    "긴장",
    "공포",
)
_DESCRIPTIVE_MARKERS = (
    "moon",
    "light",
    "shadow",
    "wind",
    "room",
    "corridor",
    "silence",
    "smell",
    "color",
    "月",
    "光",
    "影",
    "風",
    "房",
    "走廊",
    "沉默",
    "氣味",
    "빛",
    "그림자",
    "바람",
)
_NATURALNESS_PATTERNS = (
    (
        "人間",
        "NATURALNESS_PERSON_HUMAN_WORLD",
        "「人間」若表示 person/human，應改為「人」「正常人」「人類」等自然表達；只有原文確實指 human world 時才保留「人間」。",
    ),
    (
        "嘔了一口氣",
        "NATURALNESS_BREATH_ACTION",
        "「嘔了一口氣」通常不是自然中文，依語境改為「倒抽一口氣」「悶哼一聲」「吸了口氣」或「吐出一口氣」。",
    ),
    (
        "可以用十個手指頭就能數得過來",
        "NATURALNESS_REDUNDANT_COUNTING",
        "避免「可以用十個手指頭就能數得過來」這種重複結構，改為「十根手指就數得完」「幾乎十根手指就數得完」或同等自然說法。",
    ),
    (
        "觀光客人",
        "NATURALNESS_TOURIST_PERSON",
        "「觀光客人」不自然；依語境改為「觀光客」「遊客」或「旅客」。",
    ),
    (
        "纏繞在一起",
        "NATURALNESS_OVERLITERAL_ENTANGLED",
        "「纏繞在一起」若不是實際繩索或肢體纏住，應依語境改為「交錯」「糾纏」「混在一起」或更自然的描述。",
    ),
)
_NAME_PATTERN = re.compile(r"[\u4e00-\u9fff]{2,4}")


def detect_context_profile(text: str) -> ContextProfile:
    value = str(text or "").strip()
    if not value:
        return "neutral"

    lines = [line.strip() for line in value.splitlines() if line.strip()]
    dialogue_lines = sum(1 for line in lines if _looks_like_dialogue(line))
    dialogue_marks = sum(value.count(mark) for mark in _DIALOGUE_MARKS)
    dialogue_ratio = dialogue_lines / max(1, len(lines))
    lowered = value.lower()
    tension_hits = sum(1 for marker in _TENSION_MARKERS if marker in lowered or marker in value)
    descriptive_hits = sum(1 for marker in _DESCRIPTIVE_MARKERS if marker in lowered or marker in value)
    average_line_length = len(value) / max(1, len(lines))

    if dialogue_ratio >= 0.35 or dialogue_marks >= 2:
        return "dialogue_heavy"
    if tension_hits >= 2:
        return "tension"
    if descriptive_hits >= 2:
        return "descriptive"
    if len(lines) >= 3 and average_line_length >= 45:
        return "narration_heavy"
    return "neutral"


def build_context_snapshot(previous_text: str, current_text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    previous = str(previous_text or "")
    current = str(current_text or "")
    metadata = metadata or {}
    combined = "\n".join(part for part in (previous[-500:], current) if part)
    profile = detect_context_profile(current)
    naturalness_warnings = detect_naturalness_warnings(current)

    return {
        "version": CONTEXT_INTELLIGENCE_VERSION,
        "profile": profile,
        "characters": _extract_entities(combined, limit=8),
        "locations": _extract_locations(combined),
        "tone": _detect_tone(combined, profile),
        "narrative_state": _detect_narrative_state(previous, current),
        "previous_key_info": _summarize_previous(previous),
        "naturalness_warnings": naturalness_warnings,
        "metadata": dict(metadata),
    }


def build_context_directives(snapshot: dict[str, Any]) -> list[str]:
    profile = str(snapshot.get("profile") or "neutral")
    directives = [
        "Translate according to the local scene context; do not translate word-by-word when it creates stiff or unnatural Traditional Chinese.",
        "Preserve the original meaning, sequence, and emotional logic while using natural Traditional Chinese novel prose.",
        "Use context-aware phrasing for breath, reaction, and body-action descriptions; avoid literal wording that sounds physically or semantically odd.",
        "Avoid mechanical repeated structures and redundant phrasing; keep the sentence concise when the source meaning is already clear.",
        "Keep continuity with the previous chunk's characters, tone, relationship distance, and narrative state.",
    ]
    if profile == "dialogue_heavy":
        directives.append("For dialogue-heavy scenes, keep each speaker's voice distinct and avoid turning spoken lines into explanatory narration.")
    elif profile == "narration_heavy":
        directives.append("For narration-heavy scenes, prioritize smooth transitions, clear viewpoint, and readable paragraph flow.")
    elif profile == "descriptive":
        directives.append("For descriptive passages, preserve imagery and atmosphere without piling up literal modifiers.")
    elif profile == "tension":
        directives.append("For tense scenes, preserve pressure and pacing with precise, natural action verbs.")

    warnings = snapshot.get("naturalness_warnings", [])
    if isinstance(warnings, list) and warnings:
        directives.append("Naturalness Guard: avoid known awkward renderings flagged in this package; treat them as QA warnings, not forced rewrites.")
        for warning in warnings[:5]:
            if isinstance(warning, dict) and warning.get("guidance"):
                directives.append(str(warning["guidance"]))
    return directives


def apply_context_intelligence(package: dict[str, Any], current_text: str, previous_text: str | None = None) -> dict[str, Any]:
    enhanced = deepcopy(package)
    if not isinstance(enhanced, dict):
        return enhanced

    if previous_text is None:
        previous_text = _previous_text_from_package(enhanced)
    current = current_text or _source_text_from_package(enhanced)
    snapshot = build_context_snapshot(previous_text or "", current, metadata={"package_id": enhanced.get("package_id", "")})
    directives = build_context_directives(snapshot)
    _attach_context_intelligence(enhanced, snapshot, directives)
    return enhanced


def detect_naturalness_warnings(text: str) -> list[dict[str, str]]:
    return [
        {"phrase": issue["phrase"], "guidance": issue["guidance"], "severity": "warning", "risk": issue["risk"]}
        for issue in detect_unnatural_phrases(text)
    ]


def detect_unnatural_phrases(text: str) -> list[dict[str, str]]:
    value = str(text or "")
    issues: list[dict[str, str]] = []
    for phrase, code, guidance in _NATURALNESS_PATTERNS:
        if phrase in value:
            issues.append({
                "code": code,
                "phrase": phrase,
                "message": f"NATURALNESS_GUARD high-risk phrase detected: {phrase}",
                "guidance": guidance,
                "severity": "warning",
                "risk": "high",
                "confidence": "high",
            })
    return issues


def build_naturalness_repair_directives(issues: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> list[str]:
    directives: list[str] = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        guidance = issue.get("guidance")
        phrase = issue.get("phrase")
        if guidance:
            directives.append(str(guidance))
        elif phrase:
            directives.append(f"請重新處理「{phrase}」，避免生硬直譯，改用符合上下文的自然繁體中文小說表達。")
    return list(dict.fromkeys(directives))


def _attach_context_intelligence(package: dict[str, Any], snapshot: dict[str, Any], directives: list[str]) -> None:
    prompt = package.setdefault("prompt", {})
    if not isinstance(prompt, dict):
        return
    metadata = package.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        package["metadata"] = metadata

    intelligence = {
        "version": CONTEXT_INTELLIGENCE_VERSION,
        "profile": snapshot.get("profile", "neutral"),
        "snapshot": snapshot,
        "directives": directives,
        "naturalness_warnings": snapshot.get("naturalness_warnings", []),
    }
    metadata["context_intelligence"] = intelligence
    prompt["context_snapshot"] = snapshot
    prompt["context_directives"] = directives
    prompt["context_intelligence"] = intelligence
    prompt["user_prompt"] = _inject_context_directives(str(prompt.get("user_prompt", "")), snapshot, directives)

    qa = package.setdefault("qa_warnings", [])
    if isinstance(qa, list):
        for warning in snapshot.get("naturalness_warnings", []):
            if isinstance(warning, dict):
                item = {"code": "NATURALNESS_GUARD", **warning}
                if item not in qa:
                    qa.append(item)


def _inject_context_directives(user_prompt: str, snapshot: dict[str, Any], directives: list[str]) -> str:
    if CONTEXT_INTELLIGENCE_MARKER in user_prompt:
        return user_prompt

    directive_block = "\n".join(f"- {directive}" for directive in directives)
    previous = str(snapshot.get("previous_key_info") or "")
    continuity = f"previous_key_info: {previous}\n" if previous else ""
    block = (
        f"{CONTEXT_INTELLIGENCE_MARKER}\n"
        f"profile: {snapshot.get('profile', 'neutral')}\n"
        f"tone: {snapshot.get('tone', 'neutral')}\n"
        f"narrative_state: {snapshot.get('narrative_state', 'current_scene')}\n"
        f"{continuity}"
        f"{directive_block}\n"
        "[/NTPE Translation Engine v3.0 Context Intelligence]\n"
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


def _previous_text_from_package(package: dict[str, Any]) -> str:
    context = package.get("context", {})
    if isinstance(context, dict):
        for key in ("previous_chunk_tail", "previous_summary"):
            value = context.get(key)
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


def _extract_entities(text: str, limit: int) -> list[str]:
    seen: list[str] = []
    for match in _NAME_PATTERN.findall(text):
        if match in seen:
            continue
        if match in {"可以用", "十個手", "手指頭", "數得過", "正常人"}:
            continue
        seen.append(match)
        if len(seen) >= limit:
            break
    return seen


def _extract_locations(text: str) -> list[str]:
    markers = ("房間", "走廊", "門口", "街", "城", "屋", "床", "車", "room", "corridor", "street", "door")
    lowered = text.lower()
    return [marker for marker in markers if marker in text or marker in lowered][:6]


def _detect_tone(text: str, profile: ContextProfile) -> str:
    if profile == "tension":
        return "tense"
    lowered = text.lower()
    if any(marker in lowered or marker in text for marker in ("calm", "quiet", "silence", "沉默", "安靜")):
        return "restrained"
    if any(marker in lowered or marker in text for marker in ("anger", "angry", "rage", "憤怒", "怒")):
        return "heated"
    if profile == "descriptive":
        return "atmospheric"
    return "neutral"


def _detect_narrative_state(previous_text: str, current_text: str) -> str:
    if previous_text and current_text:
        return "continuing_scene"
    if current_text:
        return "current_scene"
    return "empty"


def _summarize_previous(previous_text: str, limit: int = 180) -> str:
    text = " ".join(str(previous_text or "").split())
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[-limit:]
