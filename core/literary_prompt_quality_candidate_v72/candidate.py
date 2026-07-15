from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.literary import LiteraryPromptBuilder, LiteraryPromptResult, estimate_tokens


FEATURE_FLAG = "--quality-candidate-v72"
CANDIDATE_VERSION = "7.2.0-stage12.1"
CANDIDATE_POLICY = """【TE v7.2 品質候選】
- 僅翻譯原文明示或可由語法直接確定的內容；含混處保持含混，不補時間、數量、因果、動機、關係、地點、動作或背景。
- 逐項保留敘事、動作、對話、內心與修飾；不摘要、刪節、合併或漏譯。
- 可調整語序、斷句與代詞，使繁體中文小說自然流暢，但不改資訊、語氣、因果或人物關係，不沿用生硬韓文語序。
- 依時代、場景、視角、身分與關係選詞，不強套現代台灣口語。
- 對話用「」；保留禮貌、距離、情緒、權力關係與角色口吻，不擅自強弱化。
- 沿用 glossary 與角色資料；原文僅有名或姓時，不補全名。"""


@dataclass(frozen=True)
class PromptQualityCandidateProfile:
    system_tokens: int
    policy_tokens: int
    context_tokens: int
    glossary_tokens: int
    source_tokens: int
    total_tokens: int
    total_chars: int
    candidate_enabled: bool
    candidate_version: str | None
    candidate_tokens: int
    candidate_chars: int

    def to_dict(self) -> dict[str, int | bool | str | None]:
        return self.__dict__.copy()

    def render(self) -> str:
        return (
            f"prompt_tokens total={self.total_tokens} system={self.system_tokens} "
            f"policy={self.policy_tokens} context={self.context_tokens} "
            f"glossary={self.glossary_tokens} source={self.source_tokens} "
            f"candidate={self.candidate_tokens}"
        )


@dataclass(frozen=True)
class PromptQualityCandidateResult:
    base: LiteraryPromptResult
    user_prompt: str
    prompt_profile: PromptQualityCandidateProfile
    candidate_enabled: bool

    @property
    def system_prompt(self) -> str:
        return self.base.system_prompt

    @property
    def narrative_context(self):
        return self.base.narrative_context

    @property
    def character_context(self):
        return self.base.character_context

    @property
    def glossary_context(self):
        return self.base.glossary_context

    @property
    def profile(self) -> str:
        return self.base.profile

    @property
    def prompt_compiler(self) -> dict:
        metadata = dict(self.base.prompt_compiler)
        metadata.update({
            "quality_candidate_v72_enabled": self.candidate_enabled,
            "quality_candidate_v72_version": CANDIDATE_VERSION if self.candidate_enabled else None,
            "quality_candidate_v72_tokens": self.prompt_profile.candidate_tokens,
        })
        return metadata

    def to_prompt_dict(self) -> dict:
        payload = self.base.to_prompt_dict()
        payload["user_prompt"] = self.user_prompt
        payload["prompt_profile"] = self.prompt_profile.to_dict()
        payload["prompt_compiler"] = self.prompt_compiler
        return payload


def _profile(base: LiteraryPromptResult, *, enabled: bool) -> PromptQualityCandidateProfile:
    original = base.prompt_profile
    candidate_chars = len(CANDIDATE_POLICY) if enabled else 0
    candidate_tokens = estimate_tokens(CANDIDATE_POLICY) if enabled else 0
    return PromptQualityCandidateProfile(
        system_tokens=original.system_tokens,
        policy_tokens=original.policy_tokens + candidate_tokens,
        context_tokens=original.context_tokens,
        glossary_tokens=original.glossary_tokens,
        source_tokens=original.source_tokens,
        total_tokens=original.total_tokens + candidate_tokens,
        total_chars=original.total_chars + candidate_chars,
        candidate_enabled=enabled,
        candidate_version=CANDIDATE_VERSION if enabled else None,
        candidate_tokens=candidate_tokens,
        candidate_chars=candidate_chars,
    )


def build_literary_prompt(
    *,
    chunk_text: str,
    locked_dictionary: Mapping[str, str],
    alias_map: Mapping[str, str] | None = None,
    previous_context: str = "",
    profile: str = "literary",
    candidate_enabled: bool = False,
    builder: LiteraryPromptBuilder | None = None,
) -> PromptQualityCandidateResult:
    """Build the frozen literary prompt plus one reversible Stage 12.1 policy delta."""
    base = (builder or LiteraryPromptBuilder()).build(
        chunk_text=chunk_text,
        locked_dictionary=locked_dictionary,
        alias_map=alias_map,
        previous_context=previous_context,
        profile=profile,
    )
    if not candidate_enabled:
        return PromptQualityCandidateResult(base, base.user_prompt, _profile(base, enabled=False), False)

    context_marker = "\n【Narrative】"
    if context_marker not in base.user_prompt:
        raise RuntimeError("stage121-literary-policy-boundary-unavailable")
    user_prompt = base.user_prompt.replace(
        context_marker, "\n" + CANDIDATE_POLICY + context_marker, 1,
    )
    return PromptQualityCandidateResult(base, user_prompt, _profile(base, enabled=True), True)
