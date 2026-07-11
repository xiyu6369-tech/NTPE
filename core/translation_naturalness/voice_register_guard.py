from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping

VOICE_REGISTER_GUARD_VERSION = "6.0.0-stage12.4"

ISSUE_DISCIPLINE_MAPPING = {
    "CHARACTER_VOICE_DRIFT": "CHARACTER_VOICE_CONSISTENCY",
    "HONORIFIC_REGISTER_DRIFT": "HONORIFIC_REGISTER_CONSISTENCY",
    "RELATIONSHIP_DISTANCE_DRIFT": "RELATIONSHIP_DISTANCE_CONSISTENCY",
    "NARRATIVE_VIEWPOINT_DRIFT": "NARRATIVE_VIEWPOINT_CONSISTENCY",
    "NARRATIVE_REGISTER_DRIFT": "NARRATIVE_REGISTER_CONSISTENCY",
    "ERA_INAPPROPRIATE_EXPRESSION": "ERA_REGISTER_CONSISTENCY",
    "DIALOGUE_NARRATION_REGISTER_MIX": "DIALOGUE_NARRATION_SEPARATION",
    "UNSUPPORTED_EMOTIONAL_AMPLIFICATION": "NO_ADDED_PSYCHOLOGY",
}

_MODERN = ("網紅", "直播", "按讚", "打卡", "超扯", "傻眼", "笑死", "LOL", "社群媒體", "手機")
_STRONG_EMOTION = ("怒吼", "咆哮", "暴怒", "勃然大怒", "驚恐", "嚇得魂不附體", "鄙夷", "輕蔑地")
_SOURCE_EMOTION = ("화", "분노", "소리쳤", "고함", "두려", "공포", "경멸", "怒", "恐", "輕蔑")


@dataclass(frozen=True)
class VoiceRegisterIssue:
    code: str
    severity: str
    message: str
    confidence: float
    reliable: bool
    speaker: str | None = None
    source_evidence: str = ""
    translated_evidence: str = ""
    source_start: int = -1
    source_end: int = -1
    translated_start: int = -1
    translated_end: int = -1
    locally_repairable: bool = False
    provider_retry_relevant: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code, "severity": self.severity, "message": self.message,
            "confidence": self.confidence, "reliable": self.reliable, "speaker": self.speaker,
            "source_evidence": self.source_evidence, "translated_evidence": self.translated_evidence,
            "source_start": self.source_start, "source_end": self.source_end,
            "translated_start": self.translated_start, "translated_end": self.translated_end,
            "locally_repairable": self.locally_repairable,
            "provider_retry_relevant": self.provider_retry_relevant,
            "retry_required": False, "repairable": False,
            "metadata": {"discipline_rule_code": ISSUE_DISCIPLINE_MAPPING.get(self.code),
                         "discipline_route": "warning", **self.metadata},
        }


@dataclass(frozen=True)
class VoiceRegisterGuardResult:
    version: str = VOICE_REGISTER_GUARD_VERSION
    issues: tuple[VoiceRegisterIssue, ...] = ()
    warnings: tuple[str, ...] = ()
    blocking: bool = False
    evidence_count: int = 0
    reliable_evidence_count: int = 0
    semantic_rewrite_allowed: bool = False
    provider_called: bool = False
    fail_closed: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "version": self.version, "issue_count": len(self.issues),
            "warning_count": len(self.warnings), "blocking": self.blocking,
            "evidence_count": self.evidence_count,
            "reliable_evidence_count": self.reliable_evidence_count,
            "semantic_rewrite_allowed": self.semantic_rewrite_allowed,
            "provider_called": self.provider_called, "fail_closed": self.fail_closed,
            "issues": [item.to_dict() for item in self.issues],
            "warnings": list(self.warnings), **self.metadata,
        }


def _issue(code: str, message: str, source: str, translated: str, evidence: str,
           confidence: float, speaker: str | None = None) -> VoiceRegisterIssue:
    start = translated.find(evidence)
    reliable = confidence >= .85
    return VoiceRegisterIssue(
        code, "warning", message, confidence, reliable, speaker, source[:160], evidence,
        0 if source else -1, min(len(source), 160) if source else -1,
        start, start + len(evidence) if start >= 0 else -1, False, reliable,
        {"detector": "voice_register_guard", "guard_version": VOICE_REGISTER_GUARD_VERSION},
    )


def _speaker_lines(text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for match in re.finditer(r"(?:^|\n)\s*([\u4e00-\u9fffA-Za-z·]{1,16})[：:]\s*[「『\"]?([^\n」』\"]+)", text):
        result.setdefault(match.group(1), []).append(match.group(2).strip())
    return result


def analyze_voice_register(source_text: str, translated_text: str, *, profile: str = "unspecified",
                           context: Mapping[str, Any] | None = None) -> VoiceRegisterGuardResult:
    source, translated = str(source_text or ""), str(translated_text or "")
    profile_key, context = str(profile or "unspecified").lower(), dict(context or {})
    issues: list[VoiceRegisterIssue] = []
    for speaker, lines in _speaker_lines(translated).items():
        evidence = "\n".join(lines)
        if any("您" in line for line in lines) and any("你" in line for line in lines):
            issues.append(_issue("HONORIFIC_REGISTER_DRIFT", "同一角色的敬語層級在相鄰台詞間改變。", source, translated, evidence, .91, speaker))
        formal = any(any(x in line for x in ("閣下", "請恕", "在下", "不敢")) for line in lines)
        slang = any(any(x in line for x in ("超扯", "搞啥", "笑死", "老兄")) for line in lines)
        if formal and slang:
            issues.append(_issue("CHARACTER_VOICE_DRIFT", "同一角色的正式程度與口吻出現明顯漂移。", source, translated, evidence, .88, speaker))

    narration = re.sub(r"[「『\"].*?[」』\"]", "", translated, flags=re.S)
    source_first = any(x in source for x in ("나는", "내가", "저는", "제가", "我", "我們"))
    first_match = re.search(r"(?:^|[。！？\n])\s*(我(?:們)?[^。！？\n]{0,50})", narration)
    if not source_first and first_match and any(x in source for x in ("그는", "그녀는", "그가", "그녀가")):
        issues.append(_issue("NARRATIVE_VIEWPOINT_DRIFT", "原文第三人稱敘事在旁白中無依據切換為第一人稱。", source, translated, first_match.group(1), .94))

    if any(x in profile_key for x in ("historical", "ancient", "period", "近代", "古代")):
        for term in _MODERN:
            if term.lower() in translated.lower():
                issues.append(_issue("ERA_INAPPROPRIATE_EXPRESSION", "時代設定下出現明顯現代或網路語彙。", source, translated, term, .96))

    if not any(x in source for x in _SOURCE_EMOTION):
        for term in _STRONG_EMOTION:
            if term in translated:
                issues.append(_issue("UNSUPPORTED_EMOTIONAL_AMPLIFICATION", "譯文加入原文未明示的強烈情緒。", source, translated, term, .93))

    if context.get("narrative_register") == "formal":
        for term in ("超扯", "搞啥", "有夠", "笑死"):
            if term in narration:
                issues.append(_issue("NARRATIVE_REGISTER_DRIFT", "同一場景的敘述語域由書面語突然轉為強烈口語。", source, translated, term, .86))

    reliable = sum(item.reliable for item in issues)
    return VoiceRegisterGuardResult(issues=tuple(issues), evidence_count=len(issues),
                                    reliable_evidence_count=reliable,
                                    metadata={"profile": profile_key, "discipline_mappings": dict(ISSUE_DISCIPLINE_MAPPING)})
