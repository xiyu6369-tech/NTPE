from __future__ import annotations

import hashlib
from typing import Mapping

from .model import PromptContextAnchor

ANCHOR_VERSION = "7.0.0-stage07.3"

_ZH_START = "【前文參考，僅供保持語氣與銜接，禁止重複翻譯】\n"
_ZH_END = "\n\n【待翻譯內容】"
_LITERARY_START = "【Previous】"
_LEGACY_START = "前文：\n"
_LEGACY_ENDS = ("\n待翻譯：", "\n待翻譯")
_FIXTURE_START = "CTX\n"
_FIXTURE_END = "\nSRC"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _compact_previous(value: str, limit: int = 160) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return text[-limit:]


def _failure(reason: str, *, source: str = "", strategy: str = "none") -> PromptContextAnchor:
    return PromptContextAnchor(
        version=ANCHOR_VERSION,
        strategy=strategy,
        addressable=False,
        reason=reason,
        start=-1,
        end=-1,
        content_sha256="",
        source_sha256=_sha(source),
    )


def _candidate_matches_source(candidate: str, source: str) -> bool:
    if candidate == source:
        return True
    candidate_normalized = " ".join(candidate.split())
    source_normalized = " ".join(source.split())
    if candidate_normalized == source_normalized:
        return True
    compact = _compact_previous(source)
    return bool(compact) and candidate_normalized == compact


def resolve_prompt_context_anchor(package: Mapping[str, object]) -> PromptContextAnchor:
    context = package.get("context", {})
    prompt = package.get("prompt", {})
    if not isinstance(context, Mapping) or not isinstance(prompt, Mapping):
        return _failure("invalid-package-shape")
    source = str(context.get("previous_chunk_tail", "") or "")
    user_prompt = str(prompt.get("user_prompt", "") or "")
    if not source:
        return _failure("empty-previous-context", source=source)
    if not user_prompt:
        return _failure("empty-user-prompt", source=source)

    start_count = user_prompt.count(_ZH_START)
    end_count = user_prompt.count(_ZH_END)
    if start_count == 1 and end_count == 1:
        content_start = user_prompt.index(_ZH_START) + len(_ZH_START)
        content_end = user_prompt.index(_ZH_END, content_start)
        candidate = user_prompt[content_start:content_end]
        if not _candidate_matches_source(candidate, source):
            return _failure("prompt-context-anchor-hash-mismatch", source=source, strategy="zh-section")
        return PromptContextAnchor(
            version=ANCHOR_VERSION,
            strategy="zh-section",
            addressable=True,
            reason="",
            start=content_start,
            end=content_end,
            content_sha256=_sha(candidate),
            source_sha256=_sha(source),
        )
    if start_count > 1 or end_count > 1:
        return _failure("prompt-context-anchor-ambiguous", source=source, strategy="zh-section")

    previous_count = user_prompt.count(_LITERARY_START)
    if previous_count == 1:
        content_start = user_prompt.index(_LITERARY_START) + len(_LITERARY_START)
        content_end = len(user_prompt)
        next_section = user_prompt.find("\n【", content_start)
        if next_section >= 0:
            content_end = next_section
        candidate = user_prompt[content_start:content_end].strip("\n")
        leading = len(user_prompt[content_start:content_end]) - len(user_prompt[content_start:content_end].lstrip("\n"))
        trailing = len(user_prompt[content_start:content_end]) - len(user_prompt[content_start:content_end].rstrip("\n"))
        content_start += leading
        content_end -= trailing
        if not _candidate_matches_source(candidate, source):
            return _failure("prompt-context-anchor-hash-mismatch", source=source, strategy="literary-previous")
        return PromptContextAnchor(
            version=ANCHOR_VERSION,
            strategy="literary-previous",
            addressable=True,
            reason="",
            start=content_start,
            end=content_end,
            content_sha256=_sha(candidate),
            source_sha256=_sha(source),
        )
    if previous_count > 1:
        return _failure("prompt-context-anchor-ambiguous", source=source, strategy="literary-previous")

    legacy_count = user_prompt.count(_LEGACY_START)
    matching_ends = tuple(marker for marker in _LEGACY_ENDS if user_prompt.count(marker) == 1)
    if len(matching_ends) > 1:
        matching_ends = (max(matching_ends, key=len),)
    if legacy_count == 1 and len(matching_ends) == 1:
        content_start = user_prompt.index(_LEGACY_START) + len(_LEGACY_START)
        content_end = user_prompt.index(matching_ends[0], content_start)
        candidate = user_prompt[content_start:content_end]
        if not _candidate_matches_source(candidate, source):
            return _failure("prompt-context-anchor-hash-mismatch", source=source, strategy="legacy-labeled-section")
        return PromptContextAnchor(
            version=ANCHOR_VERSION,
            strategy="legacy-labeled-section",
            addressable=True,
            reason="",
            start=content_start,
            end=content_end,
            content_sha256=_sha(candidate),
            source_sha256=_sha(source),
        )
    if legacy_count > 1 or len(matching_ends) > 1:
        return _failure("prompt-context-anchor-ambiguous", source=source, strategy="legacy-labeled-section")

    fixture_start_count = user_prompt.count(_FIXTURE_START)
    fixture_end_count = user_prompt.count(_FIXTURE_END)
    if fixture_start_count == 1 and fixture_end_count == 1:
        content_start = user_prompt.index(_FIXTURE_START) + len(_FIXTURE_START)
        content_end = user_prompt.index(_FIXTURE_END, content_start)
        candidate = user_prompt[content_start:content_end]
        if not _candidate_matches_source(candidate, source):
            return _failure("prompt-context-anchor-hash-mismatch", source=source, strategy="fixture-labeled-section")
        return PromptContextAnchor(
            version=ANCHOR_VERSION, strategy="fixture-labeled-section", addressable=True, reason="",
            start=content_start, end=content_end, content_sha256=_sha(candidate), source_sha256=_sha(source),
        )
    if fixture_start_count > 1 or fixture_end_count > 1:
        return _failure("prompt-context-anchor-ambiguous", source=source, strategy="fixture-labeled-section")
    return _failure("prompt-context-anchor-marker-missing", source=source)


def anchored_context_text(package: Mapping[str, object], anchor: PromptContextAnchor) -> str:
    if not anchor.addressable:
        return ""
    prompt = package.get("prompt", {})
    if not isinstance(prompt, Mapping):
        return ""
    user_prompt = str(prompt.get("user_prompt", "") or "")
    if anchor.start < 0 or anchor.end < anchor.start or anchor.end > len(user_prompt):
        return ""
    value = user_prompt[anchor.start:anchor.end]
    if _sha(value) != anchor.content_sha256:
        return ""
    return value


def replace_anchored_context(
    package: dict[str, object],
    anchor: PromptContextAnchor,
    replacement: str,
) -> bool:
    if not anchor.addressable or not replacement:
        return False
    prompt = package.get("prompt", {})
    context = package.get("context", {})
    if not isinstance(prompt, dict) or not isinstance(context, dict):
        return False
    user_prompt = str(prompt.get("user_prompt", "") or "")
    current = anchored_context_text(package, anchor)
    if not current:
        return False
    prefix = user_prompt[: anchor.start]
    suffix = user_prompt[anchor.end :]
    replaced = prefix + replacement + suffix
    if replaced[: anchor.start] != prefix or not replaced.endswith(suffix):
        return False
    new_prompt = dict(prompt)
    new_prompt["user_prompt"] = replaced
    new_context = dict(context)
    new_context["previous_chunk_tail"] = replacement
    new_context["prompt_context_anchor"] = {
        **anchor.to_metadata(),
        "replacement_sha256": _sha(replacement),
        "replacement_length": len(replacement),
    }
    package["prompt"] = new_prompt
    package["context"] = new_context
    return True
