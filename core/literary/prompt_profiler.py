from __future__ import annotations

from dataclasses import dataclass


def estimate_tokens(text: str) -> int:
    # Rough multilingual estimate; enough for prompt size monitoring.
    return max(1, int(len(text) / 2.4)) if text else 0


@dataclass(frozen=True)
class PromptProfile:
    system_tokens: int
    policy_tokens: int
    context_tokens: int
    glossary_tokens: int
    source_tokens: int
    total_tokens: int
    total_chars: int

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def render(self) -> str:
        return (
            f"prompt_tokens total={self.total_tokens} "
            f"system={self.system_tokens} policy={self.policy_tokens} "
            f"context={self.context_tokens} glossary={self.glossary_tokens} source={self.source_tokens}"
        )


def build_prompt_profile(*, system_prompt: str, policy_text: str, context_text: str, glossary_text: str, source_text: str) -> PromptProfile:
    system = estimate_tokens(system_prompt)
    policy = estimate_tokens(policy_text)
    context = estimate_tokens(context_text)
    glossary = estimate_tokens(glossary_text)
    source = estimate_tokens(source_text)
    return PromptProfile(
        system_tokens=system,
        policy_tokens=policy,
        context_tokens=context,
        glossary_tokens=glossary,
        source_tokens=source,
        total_tokens=system + policy + context + glossary + source,
        total_chars=sum(len(x or "") for x in (system_prompt, policy_text, context_text, glossary_text, source_text)),
    )
